# 08. 제한적 Android HAL 호환 계층

## 목적과 경계

일반 Linux 드라이버·서비스만으로 접근하기 어려운 하드웨어에 Android vendor 구성요소를 제한적으로 사용한다. Debian을 Android 안에서 실행하는 방식으로 바꾸지 않는다.

~~~text
하나의 Linux kernel
└─ host PID namespace: systemd (PID 1)
   ├─ Debian services / Xfce / Docker
   └─ LXC process (host에서 일반 PID)
      └─ container PID namespace: Android init (PID 1)
         └─ 필요한 vendor/HAL services
~~~

호스트와 컨테이너에서 PID 1이 다른 것은 PID namespace의 결과다. 컨테이너가 별도 커널이나 별도 물리 메모리 관리자를 가지는 것은 아니다.

## Android 메모리 관리에 대한 설계

| 계층 | 역할·정책 |
| --- | --- |
| Linux VM | 모든 프로세스의 메모리 할당·회수·swap·OOM 담당 |
| systemd/cgroups | 호스트에서 서비스와 컨테이너 자원 제어 |
| Android lmkd | 사용자 공간 메모리 압박 처리 데몬. 초기 HAL 구성에서 실행하지 않음 |
| legacy kernel LMK | 해당 소스·설정·모듈에 존재하는지 조사. 존재 시 Debian용 구성에서 전역 영향을 제거 |
| Zygote/system_server | Android 앱 프레임워크가 목적이 아니므로 기본 실행 대상에서 제외 |
| systemd-oomd | 초기에는 추가 정책 없이 커널/cgroup 동작을 먼저 측정 |

lmkd를 빼면 메모리 회수가 사라지는 것이 아니다. Linux 커널의 reclaim/OOM은 계속 동작한다. 반대로 PID namespace 격리만으로 kernel LMK나 전역 sysctl 영향을 막을 수 있는 것도 아니다.

실제 HAL 의존성에 추가 서비스가 필요하면 원인·역할·메모리 비용을 기록한다. 전체 Android framework를 편의상 켜는 것은 기본 전략을 변경하므로 [결정 기록](decisions.md)에 영향과 재검토를 남긴다.

## 도입 전 관문

1. 해당 기능의 표준 Linux 경로를 조사하고 구체적 장애를 기록한다.
2. 커널 문제인지 Android userspace ABI 문제인지 분리한다.
3. 필요한 최소 service·library·socket·Binder 의존성을 목록화한다.
4. kernel/vendor/Android version·ABI·firmware 조합을 고정한다.
5. 컨테이너 미실행 상태의 메모리·서비스·기능 기준을 측정한다.
6. 한 기능부터 컨테이너에 연결하고 호스트 영향을 비교한다.

기존 Halium 또는 Ubuntu Touch 포트의 성공은 일반 Debian에서의 성공 증거가 아니다. 특히 대응 Android 12 vendor·ODM 요구와 현재 ROM 사용자 공간을 혼용하지 않는다.

## 컨테이너 구성 원칙

- Debian systemd unit으로 LXC 생명주기를 관리한다.
- Android/vendor 이미지는 기본 읽기 전용으로 제공한다.
- 상태 파일과 임시 파일은 microSD의 별도 쓰기 영역에 둔다.
- 필요한 장치 노드·socket·firmware 경로만 노출한다.
- Binder device/context는 컨테이너 기능과 host bridge의 요구를 확인해 명시적으로 연결한다.
- Android init rc의 mount·chmod·chown·sysctl·cgroup·power 동작을 사전 검토한다.
- 호스트 udev와 Android ueventd가 같은 장치의 권한·소유권을 반복 변경하지 않도록 소유 범위를 정한다.
- root 권한·capability가 필요하면 이유와 영향을 기록하고 무조건 privileged 전체 노출로 시작하지 않는다.
- 컨테이너 상태 변경이 recovery·기기 고유 파티션에 쓰도록 허용하지 않는다.

특정 HAL은 강한 권한이나 공유 전역 자원을 요구할 수 있다. 이를 완전한 보안 격리라고 표현하지 않는다. kernel driver panic이나 잘못된 DMA는 호스트까지 영향을 줄 수 있다.

## 초기화 순서

기기 드라이버·펌웨어 준비 → 필요한 node/권한 준비 → Android 서비스 관리자/Binder 준비 → 기능 HAL → host bridge → 해당 Debian 서비스 순서로 의존성을 둔다.

필요한 서비스가 readiness 신호를 내기 전 단순 sleep 시간만으로 후속 서비스를 시작하지 않는다. 제한된 timeout과 실패 로그를 제공한다. HAL 없이도 SSH·기본 systemd·Docker가 올라오는 상태를 유지한다.

카메라·그래픽·오디오 bridge가 호스트 프로그램에 어떤 API를 제공하는지 기능별로 기록한다. HAL을 띄우는 것만으로 Xfce나 표준 앱이 자동으로 사용하는 것은 아니다.

## 검증

- host의 /proc/1은 systemd, container 내부 /proc/1은 의도한 init인지 확인.
- 프로세스 목록에서 lmkd·Zygote·system_server 미실행 확인.
- kernel LMK·전역 sysctl·cgroup mount·관리 주체 변화 확인.
- 컨테이너 시작 전후 PSS·cgroup memory·CPU 측정.
- HAL 서비스 재시작과 정상 종료 후 기능·호스트 서비스 상태 확인.
- host bridge가 끊김을 감지하고 로그를 남기는지 확인.
- Docker와 동시에 실행하여 네트워크·cgroup·device 권한 충돌 확인.
- 해당 드라이버가 종료·재초기화를 지원하지 않으면 무작정 강제 종료 시험을 반복하지 않고 정상 복구 경로를 준비.

## 실패와 복구

HAL 시작 실패는 해당 기능을 unavailable로 표시하고 Debian 기본 부팅은 유지한다. 부팅 전체가 HAL에 의존하게 된 경우 그 의존성을 먼저 수정한다. driver crash는 정상 kernel/DT/firmware 세트로 복귀해 최소 재현을 만든다.

완료 산출물은 service allowlist, dependency map, 이미지 provenance, 권한·마운트 목록, 메모리 비용, 장애 영향 범위, 재시작/복구 시험이다.

## 참고

- [Halium scope](https://docs.halium.org/en/latest/project/Scope.html)
- [Halium 배포판 구조](https://docs.halium.org/en/latest/Distribution.html)
- [AOSP lmkd](https://source.android.com/docs/core/perf/lmkd)
- [기존 포팅 프로젝트](https://github.com/jojobear691/ubuntu-touch-samsung-gta4lwifi)
