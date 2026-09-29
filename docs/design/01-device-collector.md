# 구현 설계 01. 기기 조사 도구

상태: 설계 확정, 코드 미구현, 실기기 수집 미실행.

이 문서는 [기기 조사 계획](../02-device-investigation.md)의 실행 도구를 정의한다. 데이터 필드·상태·종료 코드의 기준은 [데이터 계약](03-data-contracts.md)이다. 빌드 도구는 [별도 설계](02-build-artifacts.md)를 따른다.

## 1. 목적과 범위

사용자가 조사 단계를 선택하면 정해진 읽기 명령을 실행하고 원본·정규화 결과·설명 보고서를 남긴다. 결과가 불완전해도 어떤 값을 왜 얻지 못했는지 알 수 있어야 한다.

v1의 작업은 Windows/Linux에서 ADB를 통한 조사와 오프라인 보고서 생성이다. 설정·서비스·마운트·파티션을 변경하는 기기 명령은 포함하지 않는다. 기기 백업, 전체 block device 읽기, firmware/보정 데이터 추출, reboot, adb root, SELinux 변경, 도구 push는 후속 작업이다. ADB 서버 시작이나 root 관리자 인증 기록까지 전혀 상태 변화가 없다고 주장하지 않는다.

하드웨어의 실제 사용 시험은 별도 수동 확인 항목이다. 장치 노드가 있다는 이유로 터치·Bluetooth·카메라가 동작한다고 보고하지 않는다.

## 2. 구현 단위

Python 3.11 이상, 표준 라이브러리를 사용한다. 진입점은 tools/portctl.py, 내부 코드는 tools/portlib/에 둔다. 패키지를 전역 설치하지 않고 저장소에서 실행한다.

| 모듈 | 책임 |
| --- | --- |
| cli | argparse, 인수 검사, 종료 코드, 진행 메시지 |
| process | 인수 배열 실행, stdout/stderr 동시 수집, 시간·크기 제한 |
| adb | 실행 파일 탐색, 대상 선택, transport 상태, 고정 명령 전달 |
| probes | 수집 항목과 프로필 목록, 권한·형식·필수 여부 |
| parsers | 원본 바이트를 사실로 변환하는 순수 함수 |
| records | ID·JSON 계약, 원자적 저장, 증거 경로와 해시 |
| reports | private/shareable 설명 보고서 |

호스트 프로세스는 shell=False와 인수 배열을 사용한다. Android shell을 거치는 명령은 프로그램의 고정된 템플릿만 사용한다. 호스트에서 shell=False를 썼다는 사실만으로 Android 측 shell 해석까지 제거되는 것은 아니다. 사용자 입력을 원격 shell 문자열에 이어 붙이지 않는다.

## 3. CLI 계약

아래는 향후 구현할 인터페이스이며 현재 실행할 수 있는 도구가 아니다.

~~~text
python tools/portctl.py doctor --scope collect [--adb <file>]
python tools/portctl.py collect --device-alias tablet-a --profile basic [--serial <id>] [--adb <file>] [--workspace <directory>]
python tools/portctl.py collect --device-alias tablet-a --profile extended --allow-root [--serial <id>] [--adb <file>] [--workspace <directory>]
python tools/portctl.py report --run <run-directory> --view private
python tools/portctl.py report --run <run-directory> --view shareable
~~~

- scope, profile, view, device-alias는 명시적으로 받는다. device-alias는 소문자·숫자·하이픈, 1~32자로 제한한다.
- --allow-root는 extended에서만 허용한다. basic과 함께 사용하면 종료 코드 2다.
- ADB 경로는 --adb가 우선이며 없으면 PATH를 탐색한다. 명시한 경로가 실패하면 다른 ADB로 몰래 전환하지 않는다.
- workspace 기본값은 portctl.py에서 계산한 저장소 루트다. 상대 --workspace는 호출 cwd를 기준으로 절대화한다. 실제 경로는 비공개 실행 기록에만 남긴다.
- doctor는 설치 여부·버전·실행 가능성을 확인하고 콘솔에 설명한다. 설치나 기기 연결 명령은 수행하지 않는다.
- collect는 선택한 단계만 수행한다. 종료 후 다음 권장 단계와 이유를 출력하되 이어서 실행하지 않는다.
- 모든 원본과 보고서는 workspace/private/runs 아래에 생성한다. report도 이 디렉터리 안의 새 보고서 파일을 만들며 Git 추가나 외부 전송을 하지 않는다.

## 4. 대상 선택과 식별 관문

1. ADB 위치·버전을 확인한다.
2. adb devices -l 결과를 비공개 기록으로 수집한다.
3. --serial이 있으면 정확히 일치하는 대상만 선택한다. 없으면 연결 목록에 단 하나의 대상이 있을 때만 자동 선택한다. 여러 대상 중 online 한 대만 임의 선택하지 않는다.
4. 선택 대상이 device 상태인지 확인한다. unauthorized/offline/recovery/sideload는 각각 선행 조건 부족으로 종료한다.
5. 무출력 성공/실패 고정 명령으로 non-PTY shell의 remote exit status 전달을 확인한다. 이를 신뢰할 수 없으면 상세 수집을 중단한다.
6. ro.product.model과 ro.product.device를 먼저 읽는다. trim 후 모델 SM-T500, 코드명 gta4lwifi의 정확한 일치를 요구한다.
7. 불일치·누락·충돌은 identity 정보만 보존하고 종료한다. 정상 ROM의 속성 변형이 확인되면 근거를 추가해 허용 목록을 코드 변경으로 갱신한다. --force 우회는 두지 않는다.
8. 확인한 transport와 serial을 모든 후속 명령에 명시한다.

프로토콜 확인용 exit 명령은 기기 설정을 변경하지 않는 고정 진단이다. serial은 장치 선택 인수로만 쓰며 원격 명령에 포함하지 않는다. 연결이 끊기면 새 장치를 자동 선택하지 않는다.

## 5. 수집 항목

고정 probe 목록은 코드에서 정의하고 각 항목에 목적·명령·해석기·권한·상한을 연결한다. 로컬 JSON 설정으로 임의 기기 명령을 주입하는 기능은 없다.

### basic

| Probe ID | 읽기 내용 | 필수·해석 |
| --- | --- | --- |
| identity.model | getprop ro.product.model | 대상 식별 필수 |
| identity.codename | getprop ro.product.device | 대상 식별 필수 |
| identity.rom_build | getprop ro.build.fingerprint | 문자열 또는 unavailable |
| identity.vendor_build | getprop ro.vendor.build.fingerprint | kernel/HAL 대응 근거 |
| identity.bootloader | getprop ro.bootloader | 리비전 원문, 자동 펌웨어 선택 안 함 |
| boot.verified_state | getprop ro.boot.verifiedbootstate | 보고된 속성만 기록 |
| boot.vbmeta_state | getprop ro.boot.vbmeta.device_state | 잠금 해제의 단독 증거로 사용 안 함 |
| kernel.release | uname -r | 식별 이후 필수 관측 |
| kernel.version | /proc/version | 빌드 문자열 |
| boot.cmdline | /proc/cmdline | 비공개 원문, 공개 보고서에서 제외 |
| memory.info | /proc/meminfo | MemTotal·MemAvailable 등 byte로 정규화 |
| storage.partitions | /proc/partitions | 이름·major/minor·원문 크기 |
| storage.mounts | /proc/mounts | 비공개 원문, 자동 mount하지 않음 |
| storage.by_name | 알려진 두 by-name 경로의 listing | 두 결과와 불일치 보존 |
| kernel.modules | /proc/modules | 빈 목록은 정상일 수 있음 |
| input.devices | /proc/bus/input/devices | 장치명·handler·버스 정보 |

식별 통과 후 kernel.release 실패는 결과를 partial로 만들고 나머지 가능한 관측을 수집한다. basic의 다른 속성 누락도 실제 원인을 기록한다.

### extended

basic 전체와 아래 항목을 수집한다.

| Probe ID | 내용·경계 |
| --- | --- |
| kernel.config | /proc/config.gz를 바이트로 읽고 gzip 무결성 확인 |
| dt.identity | /sys/firmware/devicetree/base의 model·compatible·#address-cells·#size-cells |
| storage.resolved | by-name 링크의 실제 대상·major/minor·sysfs size, block 내용은 읽지 않음 |
| drivers.bindings | input·drm·graphics·backlight·net class의 driver/of_node 연결 |
| power.supplies | power_supply의 type·status·capacity·voltage_now·current_now·temp |
| thermal.zones | thermal zone type·temp, trip 설정에 쓰지 않음 |
| kernel.log | 한 번의 dmesg snapshot. follow/clear 옵션 사용 안 함 |

동적 발견은 지정 class 아래 1단계 항목만 열거하고 정렬한다. class당 최대 128개 항목, 항목당 명시된 attribute만 읽는다. serial·MAC·address·calibration 파일을 포괄적으로 읽지 않는다. 상세 패널 timing·전체 DT·firmware 파일 확보는 별도 조사 단계다.

sysfs size는 해당 인터페이스의 512-byte sector 규칙으로 환산하고 logical block size를 곱하지 않는다. /proc/partitions 원문 크기와 byte 값을 구분한다. DT string은 NUL 구분, integer는 big-endian cell 규칙으로 읽는다. 의미·단위가 불확실한 power 값은 원시 정수로 두고 추정 변환하지 않는다.

경로 발견 결과를 원격 명령에 사용할 때는 허용한 sysfs/proc 범위와 파일명을 검사하고 POSIX 인수 quoting을 적용한다. block 장치에 대한 cat/dd는 허용하지 않는다.

## 6. root와 바이너리 수집

extended도 일반 shell 권한부터 사용한다. permission_denied 항목이 있고 --allow-root가 있을 때 한 번의 고정 su -c 'id -u'로 UID 0 여부를 확인한다. 기본 adapter는 이 호출을 지원하는 기존 su이며 다른 문법을 추측해 반복하지 않는다.

root 확인 시간은 30초다. 거부·미지원·timeout이면 원래 결과를 보존하고 일반 관측을 계속한다. 승인 UI는 사용자가 다뤄야 한다. allow-root가 없으면 su probe 자체를 만들지 않는다.

root 재시도는 항목당 한 번이다. 일반·root 실행을 attempts에 각각 남긴다. 권한 실패가 아닌 missing file, parse_error를 root로 무조건 다시 읽지 않는다.

바이너리는 adb exec-out을 통해 stdout을 바이트로 저장하고 stderr와 분리한다. exec-out transport 성공만으로 원격 읽기 성공을 확정하지 않는다. gzip header·CRC·종료, DT cell 길이 등 형식 검증을 함께 한다. 원격 종료 상태를 얻지 못하면 remote_exit_code를 null로 둔다. 원본을 PowerShell 텍스트 리다이렉션에 통과시키지 않는다.

## 7. 실행 제한·상태 전이

~~~text
인수·환경 확인 → 대상 선택 → 식별 확인 → 순차 probe 실행
 → 원본·사실 보존 → 실행 상태 확정 → private 설명 보고서
~~~

- 일반 probe 15초, root 확인·바이너리 probe 30초. 자동 timeout 재시도는 없다.
- probe당 stdout+stderr 8MiB, 한 collect 실행의 전체 원본 64MiB 한도다.
- host에서 stdout/stderr를 동시에 읽어 pipe deadlock을 방지한다. 넘친 출력은 truncated로 기록하고 해당 로컬 ADB subprocess를 종료한다.
- 전체 한도 도달 시 나머지는 skipped/output_budget로 남기고 partial 종료한다.
- timeout 시 자기 ADB subprocess만 종료한다. adb kill-server로 다른 세션을 끊지 않는다. 원격 프로세스 종료가 입증되지 않으면 cleanup_unconfirmed를 남긴다.
- 연결 해제는 즉시 상세 수집을 중단하고 partial/device_disconnected로 종료한다. 재연결 후 수집은 새 run이다.
- Ctrl+C는 completed probe를 보존하고 interrupted로 종료한다. 자동 재시작이나 재부팅은 없다.

파일은 새 run 디렉터리에 쓰며 probe마다 event와 원본을 보존한다. 완료한 run.json은 임시 파일을 같은 디렉터리에서 rename해 게시한다. 강제 종료로 run.json이 없으면 '미종결 실행'이며 결과를 성공으로 재구성하지 않는다. report는 남은 event를 읽어 진단 요약만 만들 수 있다.

동일 workspace에서 collect는 하나만 허용한다. 잠금에는 host·PID·시각·device-alias를 기록하고 자동으로 오래된 잠금을 삭제하지 않는다. 다른 PC의 기기 제어까지 보장하는 잠금은 아니므로 실제 기기 작업자 규칙은 계속 적용한다.

## 8. 보고서와 학습 연결

private 보고서는 항목별 목적 → 실행 요약 → 관측 → 의미 → 한계 순서로 작성한다. Git revision과 원본 해시를 연결하고 다음 행동은 최대 3개로 제한한다.

자동 설명은 probe별 고정된 안내와 정규화 사실로 만든다. '이 드라이버가 원인이다'와 같은 추론은 observed에 넣지 않는다. source 후보 선택과 정상 동작 확인은 사람이 수행한 별도 기록으로 남긴다.

shareable은 허용 필드로 재구성한다. serial·MAC·원본 cmdline·raw stderr·호스트 경로는 제외한다. 허용한 문자열에도 제어문자·Markdown 삽입·식별자 패턴을 검사하고 의심 값은 withheld로 표시한다. 기기 별칭도 공개 식별자 형식일 뿐 실제 serial을 넣어서는 안 된다.

report 명령은 새 report ID의 파일을 생성한다. 기존 보고서를 덮어쓰지 않으며 원래 run의 complete/partial 상태를 숨기지 않는다. 오프라인 생성 성공은 종료 코드 0일 수 있지만 보고서 제목에 원래 partial 상태를 표시한다.

## 9. 구현 합격 기준

가짜 ADB와 합성 출력으로 다음을 먼저 검증한다. 실제 테스트 코드는 도구 구현 단계에 추가한다.

- 대상 없음·복수 대상·unauthorized·offline·모델/코드명 불일치.
- allow-root 미설정 시 su 미실행, 설정 시 필요한 항목에만 재시도.
- missing/permission/timeout/truncated/parse_error의 구별.
- 빈 /proc/modules와 빈 필수 identity를 서로 다르게 처리.
- 바이너리 gzip 정상·CRC 오류·부분 파일, DT의 NUL·endianness.
- stdout/stderr 동시 다량 출력, 전체 용량 제한, Ctrl+C·연결 해제.
- Windows 공백·한글 경로, UTF-8 외 원문 보존, fake 명령 주입 문자열.
- shareable에서 fixture serial·MAC·경로·cmdline이 노출되지 않음.
- 결과 중 하나가 실패해도 앞선 증거가 남고 새 run이 이전 run을 덮어쓰지 않음.

실기기 검증은 후속 요청 시 basic부터 수동 명령 결과와 비교한다. 그 전에는 이 문서와 fake 실행 성공을 기기 지원 증거로 표시하지 않는다.

## 참고

- [조사 계획](../02-device-investigation.md)
- [Python subprocess](https://docs.python.org/3/library/subprocess.html)
- [Android ADB 안내](https://developer.android.com/tools/adb)
