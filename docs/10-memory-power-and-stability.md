# 10. 메모리·전원·안정화

## 목표

RAM이 제한된 기기에서 GUI와 소형 서비스가 함께 동작하고, 메모리 부족·무선 끊김·절전 복귀에도 원인을 관측할 수 있게 한다. 성능 수치를 미리 성공 조건으로 꾸미지 않고 실제 측정 기준을 만든다.

충전과 온도 보호는 첫 실기기 부팅부터 관측한다. 배터리 제거·충전 회로 변경·thermal 제한 해제는 범위 밖이다.

## 메모리 측정

각 이미지에서 부팅 후 안정화 시간을 일정하게 두고 다음 네 상태를 측정한다.

1. Debian 기본 서비스.
2. Xfce 추가.
3. 필요한 HAL 추가.
4. 기준 웹/API 컨테이너 추가.

같은 밝기·네트워크·GUI 상태를 사용하고 백그라운드 업데이트 여부를 기록한다. MemAvailable, 프로세스 PSS, slab, page cache, cgroup memory, swap/zram, CPU, 지원되는 pressure 지표를 수집한다.

free의 used 값만으로 서비스 메모리를 비교하지 않는다. GPU/DSP reserved memory와 driver allocation은 프로세스 RSS에 온전히 나타나지 않을 수 있다. cgroup 집계와 전체 사용량 차이도 조사한다.

## 자원 제어·OOM

[Docker 기준 제한](09-debian-desktop-and-containers.md)을 사용하고, 메모리·PID 초과 시험은 제한된 시험 컨테이너에서 수행한다. 처음부터 호스트 전체 RAM을 고갈시키지 않는다.

목표는 시험 프로세스가 제한에 걸려도 host SSH와 GUI가 살아 있고 kernel/cgroup 로그로 원인을 설명할 수 있는 것이다. memory limit·swap 정책·oom-kill 기록을 함께 남긴다.

Android lmkd는 기본 실행하지 않는다. legacy kernel LMK와 vendor 정책이 존재하는지 [HAL 문서](08-android-hal-compatibility.md)에 따라 조사한다. systemd-oomd 같은 추가 정책은 초기에는 끄고 커널·cgroup의 기본 동작을 측정한다. 호스트 OOM 처리 자체를 비활성화하지 않는다.

HAL cgroup의 강제 메모리 상한은 실제 peak와 기능 실패를 측정한 뒤 정한다. 근거 없는 낮은 상한으로 카메라·GPU 초기화를 깨뜨리지 않는다.

## zram·저장소

자원 제한 시험을 먼저 통과한 뒤 zram을 추가한다. 초기 논리 크기는 실제 MemTotal의 25%, 최대 768MiB다. 지원되는 경우 LZ4를 기본으로 하고 실제 압축률·CPU 비용을 기록한다.

zram 논리 크기가 곧 RAM 선점량이라고 설명하지 않는다. 원본·압축·총 메모리 사용량을 구분한다. microSD swap과 zram writeback은 초기에는 사용하지 않는다.

ext4 journal을 끄거나 파일시스템 보호를 제거해 성능을 올리지 않는다. 로그 크기와 Docker 이미지 수를 제한하고 남은 용량을 모니터링한다. SD 수명·I/O latency가 병목이면 서비스를 줄이거나 장기적으로 저장소 설계를 재검토한다.

## 전원 관측

power_supply의 status·capacity·voltage·current·temperature는 드라이버별 단위와 부호를 확인한다. 수치를 다른 기기의 기준으로 해석하지 않는다. 가능하면 같은 기기의 정상 Android 관측값과 비교한다.

충전 cable 연결/해제, 배터리 잔량 추세, 화면 밝기 변화, CPU 부하, thermal throttling을 단계적으로 시험한다. 제조사 안전 한계는 유지한다. 비정상 발열·충전 불안정·센서 이상 시 부하를 종료하고 정상 이미지로 복귀한다.

충전기 연결 상태에서만 부팅되는 문제와 배터리 전원 부팅을 구분한다. poweroff 후 충전 화면/충전 동작도 전체 기능표에 남긴다.

## 태블릿·서버 모드

| 모드 | 서비스 | 전원 정책 |
| --- | --- | --- |
| 태블릿 | GUI, 필요한 하드웨어 서비스 | 초기에는 화면만 끔. suspend 검증 후 자동 절전 활성화 |
| 서버 | GUI 선택 + 기준 웹/API 작업 | 작업 실행 중 systemd-logind sleep inhibitor, 화면 끄기는 허용 |

Docker daemon이 떠 있다는 이유만으로 절전을 막지 않는다. 프로젝트 서버 작업을 관리하는 systemd unit 또는 wrapper가 작업 수명 동안 inhibitor를 유지한다. 작업 중지 시 inhibitor를 해제한다. Xfce에서 현재 모드와 전환 항목을 볼 수 있게 한다.

수동 suspend 요청도 활성 서버 작업에 영향이 있음을 UI/로그에 보여 준다. 자의적으로 서비스를 죽이거나 저장하지 않은 GUI 작업을 종료하지 않는다.

## suspend/resume 순서

1. 먼저 화면 blank/unblank와 터치 복귀를 검증한다.
2. 실제 커널의 suspend state·wakeup source·pm 로그 인터페이스를 조사한다.
3. USB 콘솔 연결 유무가 suspend를 방해하는지 확인한다.
4. 단일 suspend/resume에서 SD·화면·입력·무선·오디오 상태를 검사한다.
5. 반복 시험을 늘려 누적 실패·배터리 소모를 관측한다.
6. Wi-Fi·Bluetooth·컨테이너가 함께 있을 때 다시 검증한다.

기존 cmdline의 lpm_levels.sleep_disabled 같은 설정은 의미와 현재 동작을 조사한 뒤 변경한다. 문자열 삭제만으로 정상 deep sleep이 된다고 판단하지 않는다. runtime PM, 화면 끄기, system suspend를 별개의 상태로 기록한다.

## 안정화 시험·산출물

장시간 GUI+서버 부하, 무선 재연결, 정상 종료, 부팅 반복, 절전 복귀를 [11 기준](11-validation-and-milestones.md)으로 수행한다. 로그에는 이미지 ID·기온·전원·밝기·서비스·실제 가동 시간을 남긴다.

의도적 전원 차단이나 파일시스템 손상은 일상 데이터가 없는 별도 SD/복제 이미지에서만 시험한다. kernel/firmware 문제가 해결되기 전 벤치마크 성능 수치만 최적화하지 않는다.

## 참고

- [cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html): 구형 커널의 실제 지원과 대조한다.
- [Linux 전원 관리](https://docs.kernel.org/power/index.html)
- [zram](https://docs.kernel.org/admin-guide/blockdev/zram.html)
