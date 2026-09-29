# 02. 기기 조사와 기준표

## 목표·진입 조건

실험 대상을 정확히 식별하고 정상 동작·이미지·펌웨어의 기준을 만든다. 기기 변경 없이 확인할 수 있는 정보를 먼저 수집한다. ADB가 없다면 공식 Platform Tools 준비와 기기 연결을 선행하며 설치·USB 디버깅 설정 변경은 조사와 구분해 기록한다.

현재 확인된 것은 사용자의 기기 상태 설명뿐이다. 아래 명령은 **향후 실행할 읽기 전용 예시**이고 아직 실행 결과가 없다. ADB 연결 과정에서 호스트 ADB 서버가 시작될 수 있지만 파티션 기록·재부팅 명령은 포함하지 않는다.

## 수집 순서

1. 케이블·USB 인식·ADB 버전과 인증 상태 확인.
2. 정확한 모델·코드명·ROM·vendor·bootloader 확인.
3. 커널·cmdline·설정·모듈 확인.
4. 파티션 이름·장치 매핑·용량·파일시스템 확인.
5. DT·입력·그래픽·무선·전원 드라이버 확인.
6. 정상 기능 시험 및 부팅 로그 확보.
7. [백업 문서](03-backup-and-recovery.md)에 필요한 정확한 대상을 전달.

## 기본 조사 명령

PowerShell에서 ADB 경로를 확인한 뒤 실행한다. 여러 기기가 연결되어 있으면 모든 기기 명령에 -s와 확인한 대상 식별자를 추가한다. 식별자는 공유 로그에서 마스킹한다.

~~~powershell
adb version
adb devices -l
adb shell getprop ro.product.model
adb shell getprop ro.product.device
adb shell getprop ro.build.fingerprint
adb shell getprop ro.vendor.build.fingerprint
adb shell getprop ro.bootloader
adb shell getprop ro.boot.verifiedbootstate
adb shell getprop ro.boot.vbmeta.device_state
adb shell uname -a
adb shell cat /proc/version
adb shell cat /proc/cmdline
adb shell cat /proc/meminfo
adb shell cat /proc/partitions
adb shell cat /proc/mounts
adb shell ls -l /dev/block/by-name
adb shell ls -l /dev/block/bootdevice/by-name
adb shell cat /proc/modules
adb shell cat /proc/bus/input/devices
~~~

일부 속성이 비어 있거나 경로가 없을 수 있다. 빈 값은 '미확인/해당 인터페이스 없음'으로 기록하며 실패한 명령을 반복하지 않는다. 전체 getprop 덤프보다 필요한 항목을 우선 수집한다.

root 접근이 필요한 읽기는 현재 설치된 root 관리자의 정책을 따른다. 조사 편의를 위해 SELinux를 끄거나 adbd 설정을 바꾸지 않는다. 사용자 승인이 필요한 root 팝업이 나오면 무인 접근이 가능하다고 가정하지 않는다.

## 커널·이미지 조사

- /proc/config.gz가 있으면 바이너리 그대로 확보하고 개발 PC에서 압축 해제한다.
- 없으면 ROM 빌드 산출물, kernel image의 embedded config, 대응 소스 설정 순서로 조사한다.
- PowerShell 텍스트 리다이렉션으로 바이너리 이미지를 저장하지 않는다. 검증된 바이너리 전송 방식과 해시 검사를 사용한다.
- boot/recovery 이미지의 확보는 [백업 절차](03-backup-and-recovery.md)로 수행한다.
- 정상 boot의 커널·ramdisk·DTB·헤더·AVB 관련 영역을 각각 분석한다.
- /proc/cmdline과 이미지 cmdline이 다른 경우 부트로더가 추가한 값을 구분한다.
- 모듈은 이름·파일 위치·vermagic·의존성·출처를 함께 기록한다.

## 파티션·DT 조사

by-name 심볼릭 링크를 실제 block device로 해석하고 크기를 바이트 단위로 기록한다. /dev/block/mmcblk0pN 같은 번호를 계획에 고정하지 않는다.

vendor·odm·system 등이 super의 논리 파티션인지 확인한다. Android의 동적 파티션을 일반 ext4 파티션처럼 바로 마운트할 수 있다고 가정하지 않는다.

실행 중 DT는 /sys/firmware/devicetree/base 등 제공되는 인터페이스로 조사한다. compatible의 NUL 구분과 주소 cell 형식을 고려하고, DT 문자열을 일반 텍스트처럼 일괄 처리하지 않는다.

예약 메모리, ramoops, 패널·터치 노드, SD 컨트롤러, USB, regulator·clock 연결을 우선 확인한다. decompile한 DTS는 비교 자료이며 원본 소스를 대체하지 않는다.

## 부품·정상 동작 조사

| 영역 | 관측할 내용 |
| --- | --- |
| 화면 | 패널 이름, 해상도, 백라이트 노드, DRM/fb 장치, 회전 |
| 터치 | input 장치 이름, event 노드, 버스·드라이버, 펌웨어 이름 |
| Wi-Fi | 모듈, 펌웨어 경로, 보정 데이터 의존성, 지원 모드 |
| Bluetooth | 전원 장치, transport, Android vendor 서비스, firmware |
| 오디오 | ALSA 카드·PCM·mixer, DSP·모듈 의존성 |
| 카메라 | 전후면 센서, 장치 노드, ISP·HAL 관련 서비스 |
| 센서·GPS | 실제 탑재 목록, IIO/input/vendor 경로, 정상 동작 |
| 전원 | 배터리·충전·thermal·cpufreq·wakeup source 인터페이스 |
| 저장소·USB | microSD 동작, OTG 장치, 데이터·충전 역할 |

공개 커널에 Himax 설정이 있다고 실제 기기도 Himax라고 확정하지 않는다. 부품 변형을 런타임 바인딩·DT·로그로 확인한다.

## 기준표 양식

~~~text
조사 ID / 시각 / 조사자:
기기 별칭(민감 식별자 제외):
모델 / 코드명 / ROM / vendor / bootloader:
커널 / source 후보 / config 출처:
부팅 이미지 ID / 헤더 보고서 / DT 해시:
파티션 표 위치 / 읽기 권한 제한:
실제 RAM / microSD 용량·식별 방법:
실제 부품·바인딩 표:
정상 기능 / 기존에 고장 난 기능:
원본 로그 비공개 위치 / 공유용 로그 위치:
미확인 사항 / 다음 읽기 전용 조사:
~~~

## 완료 조건·실패 대응

모델 식별, boot/recovery 대상과 크기, 현재 ROM·vendor·kernel 관계, 정상 기능표, 수집 자료의 출처가 있어야 기준표 완료다. 부족한 root 권한이나 소스 대응 정보는 차단 항목으로 표시한다.

ADB 미인식은 케이블·USB 장치 인식·드라이버·인증 순서로 조사한다. 모델·파티션 불명확 상태에서는 기록 단계로 넘어가지 않는다. 현재 ROM 소스가 없으면 검증 가능한 공개 빌드로 기준을 바꾸는 [커널 재현 절차](06-kernel-porting.md)를 따른다.

## 참고

- [LineageOS SM-T500 정의](https://github.com/LineageOS/lineage_wiki/blob/main/_data/devices/gta4lwifi.yml)
- [공개 fstab](https://github.com/LineageOS/android_device_samsung_gta4l-common/blob/lineage-23.2/init/fstab.emmc)
- [기기별 커널 설정](https://github.com/LineageOS/android_kernel_samsung_sm6115/blob/lineage-23.2/arch/arm64/configs/vendor/gta4l-common.config)
