# 01. 목표와 아키텍처

## 목적과 성공 정의

SM-T500을 일반 Linux 사용자 공간을 실행하는 터치 태블릿 겸 소형 개발 서버로 만든다. 포팅 결과뿐 아니라 부팅·드라이버·메모리·전원 구조를 설명할 수 있는 학습 산출물을 남긴다.

첫 시제품은 Nura 26.06의 systemd를 호스트 PID 1로 실행하고 Xfce·터치·Wi-Fi·Bluetooth와 ARM64 웹/API 컨테이너를 사용할 수 있는 상태다. [D014](decisions.md)와 [포팅 계획](14-nura-26.06-port-plan.md)에 따라 공식 공통 기반에 SM-T500 지원을 추가한다. 전체 완료는 실제 탑재 기능을 모두 조사하고 [기능표](07-hardware-enablement.md)와 [검증 기준](11-validation-and-milestones.md)을 충족한 상태다.

미지원 기능은 포기하거나 숨기지 않는다. '미조사', '구현 중', '부분 동작', '검증 완료', '차단됨'을 구분하고 필요한 자료와 다음 가설을 남긴다. 모든 하드웨어 지원의 성공 시점은 보장하지 않는다.

## 용어

| 용어 | 이 프로젝트에서의 의미 |
| --- | --- |
| 네이티브 Linux | 물리 기기에서 Linux 커널과 일반 Linux 호스트 사용자 공간을 직접 실행. 현재 호스트 기준은 Nura 26.06 |
| 공식 기본 이미지 | Nura v26.06/aarch64 공식 패키지·기본 구성으로 생성할 rootfs. SM-T500 전용 kernel·DT·기기 설정을 따로 연결 |
| 제조사 커널 | Samsung/QCOM/LineageOS의 기기 지원 수정이 들어간 커널 |
| 메인라인 | upstream Linux 기반 보드·드라이버 지원. 단순히 버전 번호가 높은 커널을 뜻하지 않음 |
| 펌웨어 | 무선·DSP·터치 등 하드웨어에서 실행하거나 로딩하는 바이너리 |
| Android HAL | Android용 드라이버 접근·vendor 서비스 인터페이스. Linux 호스트를 대체하지 않음 |
| 복구 | 정상 OS로 돌아가는 절차. Knox 보안 상태의 원복과는 별개 |

## 목표 구조

~~~text
Samsung bootloader
  └─ 호환되는 mainline/LTS kernel + DTB/DTBO + Nura initramfs
      └─ microSD ext4 Nura 26.06 rootfs
          └─ systemd (host PID 1)
              ├─ udev / SSH / NetworkManager
              ├─ Xorg / Xfce / touch keyboard
              ├─ Docker Engine → web / API
              └─ optional LXC → Android init → required HAL services
~~~

기존 부트로더가 microSD를 직접 부팅한다는 가정은 하지 않는다. 내부 boot 이미지의 커널이 SD를 읽고 rootfs를 선택한다. GRUB·UEFI·fastboot 임시 부팅도 초기 전제에 포함하지 않는다.

## 구성 선택

- 초기 배포판은 Nura 26.06 aarch64다. 공식 v26.06 패키지·기본 구성을 사용하고 기존 Tab A7 rootfs·오래된 kernel을 통째로 상속하지 않는다.
- 메모리 사용량은 배포판 이름보다 패키지·GUI·상주 서비스 구성으로 관리한다.
- 배포판 지원이 커스텀 kernel·SM-T500 하드웨어 지원까지 보장하지는 않는다. 릴리스 업데이트는 정상 세트와 구분해 별도 검증한다.
- GUI는 Xfce/X11, 초기 합성 효과 비활성화, Onboard 화면 키보드가 기본이다.
- Docker는 Linux Engine을 사용한다. 태블릿에 Docker Desktop이나 KVM 가상화를 요구하지 않는다.
- 일반 Linux API를 우선하고 필요한 기능에만 제한적 HAL을 도입한다.
- 유지되는 mainline/LTS를 초기 kernel 후보로 평가하고 정상 One UI·복구 이미지는 별도로 보존한다. 제공 순정 자료는 기기 배선·firmware·동작 비교에 사용한다.

## 우선순위와 범위

1. 읽기 전용 조사, 백업, 복구 경로.
2. 공식 Nura 기준·도구 고정, 필요한 SM-T500 정보/코드 선별, 화면 없이도 로그와 셸 확보.
3. Nura systemd·SSH·Docker.
4. 화면·터치·Wi-Fi·Bluetooth.
5. GPU·오디오·카메라·센서·GPS·전원·절전 등 전체 기능.
6. upstream 지원·Nura 업데이트·장기 유지.

충전·온도 보호의 기본 확인은 첫 실기기 부팅부터 수행한다. 최적화와 깊은 절전만 후속 단계로 둔다. 블루투스가 막혀도 독립적인 학습·기능 작업은 계속할 수 있다.

기본 범위 밖은 기기 분해·UART·납땜, 부트로더 교체, 파티션 테이블 재구성, 내부 저장소 Linux 설치, Android 앱 실행 환경, 자동 원격 플래싱, 완전한 듀얼부팅 메뉴다. 추가 요구가 생기면 영향과 복구 조건을 검토해 결정 기록을 갱신한다.

## 사실과 가정의 구분

| 구분 | 현재 내용 |
| --- | --- |
| 사용자 확인 | SM-T500, 부트로더 해제·루팅된 LineageOS, microSD, C 가능·커널 입문, 하루 약 2시간 |
| PC 관측 | Windows, WSL2 Ubuntu 24.04 설치, 초기 저장소에 코드 없음 |
| 공개 자료 | SM6115, 4.19 계열, boot header v2, 별도 recovery 등 |
| 기기 미확인 | 현재 커널·ROM·vendor·boot 헤더·파티션·실제 RAM·패널·터치 부품 |
| 채택한 OS 기준 | Nura 26.06/aarch64, 기존 Tab A7 지원은 필요한 부분만 선별 이식 |
| 유지하는 기본값 | Xfce, microSD ext4, 제한적 HAL, 컨테이너 기준 부하 |

## 참고

- [Nura 26.06 발표](https://nura.eco/blog/2026/06/21/v26.06-release/)
- [LineageOS 기기 정의](https://github.com/LineageOS/lineage_wiki/blob/main/_data/devices/gta4lwifi.yml)
- [Halium 구조](https://docs.halium.org/en/latest/Distribution.html)
- [설계 결정 기록](decisions.md)
