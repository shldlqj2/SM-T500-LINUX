# 07. 하드웨어 기능 구현

## 원칙·진입 조건

USB 진단 또는 SSH와 정상 복구 이미지가 준비된 뒤 기능별 실험을 시작한다. 충전·온도 기본 관측은 첫 부팅부터 진행한다. 공개 기기 사양의 기능을 그대로 탑재 목록으로 확정하지 않고 [기기 조사](02-device-investigation.md)로 실제 목록을 만든다.

각 기능은 미조사 → 의존성 파악 → 구현 중 → 단독 검증 → 통합 검증 순서로 관리한다. '드라이버 로딩 성공', '장치 노드 존재', '앱에서 기능 사용'을 구분한다.

## 지원표 초기 상태

아래 상태는 문서 작성 시점의 실제 값이다. 기존 LineageOS에서의 기능도 아직 직접 검사하지 않았다.

| 기능 | 우선순위 | Debian 상태 | 주요 의존성 | 대표 증거 |
| --- | --- | --- | --- | --- |
| 기본 배터리·충전·thermal | 초기 안전 관측 | 미조사 | PMIC, gauge, charger, DT | 상태·온도·충전 추세 |
| microSD | P0 부팅 | 미조사 | MMC host·전원·ext4 | UUID·읽기·쓰기 |
| USB 진단 | P0 부팅 | 미조사 | PHY, DWC3, gadget, configfs | ACM 콘솔·SSH |
| 화면·백라이트 | P1 | 미조사 | panel, DSI, display, regulator | 패턴 출력·밝기 |
| 터치·버튼 | P1 | 미조사 | I2C/SPI, GPIO IRQ, firmware | evdev·GUI 조작 |
| Wi-Fi | P1 | 미조사 | WLAN 모듈, firmware, calibration | 연결·재연결·전송 |
| Bluetooth | P1 | 미조사 | transport, power, firmware, HCI/HAL | 입력·BLE·오디오 |
| GPU | P2 | 미조사 | KGSL 또는 DRM/MSM, userspace ABI | renderer·3D 부하 |
| 오디오 | P2 | 미조사 | DSP, ALSA/ASoC, mixer, routing | 녹음·재생·경로 전환 |
| 전후면 카메라 | P2 | 미조사 | sensor, ISP, firmware, HAL/media | preview·사진·영상 |
| 영상 코덱 | P2 | 미조사 | media driver·codec firmware | HW decode/encode 관측 |
| 센서·위치 | P2 | 미조사 | IIO/input/HAL, DSP/GNSS | 회전·실외 위치 |
| USB OTG | P2 | 미조사 | role switch·전원·host | 키보드·저장소 |
| CPU/GPU 주파수·절전 | P2 | 미조사 | cpufreq/devfreq, wakeup, PM | 주파수·전력·복귀 |
| RTC·시간·종료 | P2 | 미조사 | RTC, NTP, poweroff | 시간 유지·정상 종료 |

P2는 제외 기능이 아니다. 탑재하지 않은 기능은 증거와 함께 '해당 없음'으로 표시한다. 알려지지 않은 부품은 모델명 추정 대신 조사 과제로 남긴다.

## 공통 드라이버 분석 양식

~~~text
기능 / 실제 부품 / 하드웨어 변형:
DT node·compatible / bus / driver source:
전원·clock·reset·GPIO·IRQ 의존성:
모듈·firmware·보정 데이터 / 출처·해시:
probe 로그 / 실패 errno / deferred 공급자:
사용자 공간 API / 필요한 서비스:
단독 시험 / 통합 시험 / 현재 제한:
표준 Linux 경로의 장애 / HAL 필요성:
다음 가설 / 정상 복귀 세트:
~~~

## 화면·터치

패널·백라이트부터 켜고 단색/패턴 화면을 검증한다. DRM 노드 존재만으로 표준 KMS 사용 가능을 단정하지 않는다. connector·mode·buffer 할당·scanout을 확인한 뒤 Xorg modesetting 경로를 시도한다. fbdev가 실제 동작하면 초기 Xfce 소프트웨어 렌더링에 활용한다.

터치는 input 장치 이벤트부터 검사한다. IRQ 미발생, firmware 오류, 좌표 범위 오류, 화면 변환 오류를 분리한다. 드라이버 재로딩이 터치 firmware flash를 일으키는지 확인하고 불필요한 영구 쓰기를 피한다.

가로·세로 출력 회전과 터치 좌표 행렬을 함께 변경한다. edge·multitouch·드래그·키보드 호출을 시험한다. 화면이 정상이어도 터치/키보드 없는 로그인 화면이면 완료가 아니다. [GUI 구성](09-debian-desktop-and-containers.md)을 따른다.

## Wi-Fi

1. 정확한 대응 모듈과 의존 모듈 설치.
2. firmware·calibration 경로 및 로딩 권한 확인.
3. 필요한 전원/서비스 초기화 후 wlan 인터페이스 확인.
4. rfkill·regulatory 상태 확인.
5. wpa_supplicant·NetworkManager 연결.
6. 재부팅·AP 전환·장시간 전송·Bluetooth 동시 사용.

MAC·보정 파일은 해당 기기의 자료만 사용한다. Android의 Wi-Fi HAL이 없어서 생기는 차이와 드라이버 자체 오류를 구분한다. 기본 STA 연결 후 AP·P2P 등 실제 기기의 부가 기능도 후속 지원표에 추가한다.

## Bluetooth

전원 control·transport·펌웨어·vendor initialization 경로를 먼저 찾는다. /dev 장치명만 보고 표준 UART Bluetooth라고 가정하지 않는다.

표준 HCI 연결이 되면 BlueZ를 직접 사용한다. 불가능하면 [제한적 HAL](08-android-hal-compatibility.md)로 Android Bluetooth 인터페이스와 BlueZ 사이 bridge를 검토한다. HCI/VHCI bridge 동작, management event, L2CAP·HID를 단계별로 관측한다.

초기 합격은 입력 장치 페어링·입력·재접속이다. 이후 BLE, 오디오, Wi-Fi 공존, 절전 복귀를 각각 시험한다. 참고 Ubuntu Touch 포트도 Bluetooth를 실험 단계로 표기하므로 패치를 그대로 안정 버전으로 취급하지 않는다.

## GPU·미디어

제조사 KGSL과 upstream DRM/MSM은 userspace ABI가 다르다. GPU 이름이 Adreno라는 이유만으로 일반 Mesa 설치가 가속을 제공한다고 판단하지 않는다. DRM/render node 또는 KGSL 인터페이스, 실제 renderer, buffer 공유 경로를 확인한다.

GPU 가속 경로는 표준 지원 여부 조사 → 호환 라이브러리 필요성 → 제한적 호환 또는 메인라인 순서로 평가한다. unsupported ioctl을 에러 없이 무시하는 패치는 기능 성공으로 인정하지 않는다.

오디오는 ALSA 카드·PCM 확인, DSP firmware·모듈, mixer route, 출력 gain을 분리한다. 낮은 볼륨에서 스피커·이어폰·마이크를 시험하고 정상 상태의 routing을 기록한다. UCM/ALSA에서 부족하면 최소 Audio HAL 경로를 검토한다.

카메라는 sensor probe만으로 완료가 아니다. ISP·memory buffer·HAL·media bridge·앱 경로까지 필요하다. 표준 V4L2 제공 여부를 먼저 조사하고 droidmedia 등 기존 포트의 경로는 별도 의존성 검증 후 활용한다. 전후면·사진·영상·codec 가속을 나눠 기록한다.

## 센서·GPS·USB·전원

센서는 실제 IIO/input 또는 HAL 경로와 unit·축 방향을 확인한다. 자동 회전은 화면·터치 변환까지 통합 검증한다. GPS는 적절한 실외 조건에서 fix·재획득을 확인하고 네트워크 위치 결과와 구분한다.

USB host 시험은 Wi-Fi SSH를 확보한 뒤 진행한다. 한 포트의 gadget·host 전환으로 진단 연결이 끊기는 것을 예상하며 연결한 저장장치의 mount·unmount와 전원 역할을 확인한다.

충전·thermal·cpufreq·suspend 정책은 [전원 문서](10-memory-power-and-stability.md)를 따른다. 보호 기능을 꺼서 부하 시험을 통과시키지 않는다.

## 완료와 추적

각 기능마다 최소 한 개의 소스·설정 근거, 단독 시험 로그, 재부팅 후 동작, 통합 회귀 결과가 있어야 '검증 완료'로 바꾼다. 일시 성공·특정 기기만 성공·일부 프로필만 성공은 제한을 명시한다.

## 참고

- [LineageOS 공통 보드 설정과 모듈 목록](https://github.com/LineageOS/android_device_samsung_gta4l-common/blob/lineage-23.2/BoardConfigCommon.mk)
- [SM-T500 Ubuntu Touch 기능 현황](https://github.com/jojobear691/ubuntu-touch-samsung-gta4lwifi)
- [Linux 드라이버 모델](https://docs.kernel.org/driver-api/driver-model/index.html)
