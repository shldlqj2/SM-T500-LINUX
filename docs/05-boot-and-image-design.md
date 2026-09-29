# 05. 부팅 경로와 이미지 계약

## 목적·선행 조건

검증된 boot 이미지 구조를 보존하면서 Android init 대신 자체 initramfs와 Debian을 실행한다. [기기 기준표](02-device-investigation.md), [복구 관문](03-backup-and-recovery.md), 대응 이미지 확보가 선행 조건이다.

## 공개 자료와 실제 기준

공개 LineageOS 구성은 header v2, Image.gz, boot 내 DTB, 별도 DTBO·recovery를 사용한다. A/B OTA는 비활성화되어 있다. 이 정보는 조사 출발점이며 현재 기기의 header·크기·offset·AVB 상태를 대체하지 않는다.

LineageOS BoardConfigCommon의 ramdisk offset 표기는 0x020000000이고 참고 Ubuntu Touch deviceinfo는 0x02000000이다. 어느 값을 임의로 정답이라 고르지 않는다. 정상 이미지 분석 결과와 검증된 build recipe를 기준으로 차이를 해소한다.

현재 확인하지 않은 값에는 기본값을 넣지 않는다. mkbootimg의 offset 값과 실제 물리 배치, DT reserved-memory 주소도 구분한다.

## 이미지 분석·조립 순서

1. 원본 전체 파일의 크기·해시·출처 보존.
2. header 버전·page size·board·cmdline·각 영역 크기·offset 추출.
3. 커널 압축 형식, ramdisk 압축·cpio, DTB 목록과 DTBO 관계 확인.
4. AVB footer/descriptor 및 vendor별 추가 서명·metadata 영역 조사.
5. payload를 수정하지 않고 재조립.
6. 원본과 header·payload·padding·서명 차이를 분리 비교.
7. 정적 검사 통과 후 복구 가능한 조건에서 재패키징 이미지 부팅 시험.

재조립 결과의 전체 해시 차이만으로 실패라 판정하지 않는다. 압축 시각·cpio metadata 등 차이의 이유를 설명해야 한다. 반대로 도구의 성공 메시지만으로 수용하지 않는다.

현재 AVB 설정이 custom image를 허용한다는 것을 부트로더 해제 여부만으로 단정하지 않는다. 정상 커스텀 이미지와 metadata를 분석하며, 빈 vbmeta 등 다른 프로젝트의 이미지를 무조건 기록하지 않는다.

## 이미지 세트의 필수 필드

| 항목 | 요구 |
| --- | --- |
| 식별 | build ID, 모델·코드명, 생성 시각, 목적 |
| 출처 | 각 저장소 SHA, patch 목록, toolchain ID |
| 커널 | release, 최종 config 해시, Image 해시 |
| 모듈 | release별 디렉터리, 파일 목록·해시, vermagic·심볼 대응 |
| DT | DTB/DTBO 원본·해시·선택 근거 |
| initramfs | 소스 버전·압축 형식·내용 명세·해시 |
| rootfs | 배포판·패키지 명세·UUID·호환 build ID |
| 펌웨어 | 파일 출처·경로·해시·기기 고유 데이터 의존성 |
| 기록 | 허용 대상 파티션 이름·실측 크기·이미지 크기·헤더 보고서 |
| 복귀 | 마지막 정상 이미지 ID·위치·복구 문서 |

manifest의 정확한 JSON 키 등 구현 형식은 도구 구현 시 위 필드를 그대로 반영한다. 문서만 작성하는 단계에서 자동 flash용 wire format을 추가하지 않는다.

## initramfs 설계

초기 /init은 정적 BusyBox 기반이다. 핵심 기능은 디버깅과 rootfs 전환이며 Android 서비스를 실행하지 않는다.

~~~text
PID 1 /init
  → proc / sysfs / devtmpfs / run 준비
  → 부팅 단계 로그, USB ACM 진단 준비
  → 필요한 모듈·펌웨어 준비
  → 지정 UUID의 SD rootfs 탐색 (기본 30초)
  → 읽기 전용 mount와 marker·init·호환 manifest 검사
  → 검증된 정상 rootfs로 전환
  → exec switch_root ... /sbin/init
~~~

MMC·SD host·clock·regulator·partition parser·ext4와 USB 진단 의존성은 built-in을 우선한다. 모듈이 필요하면 initramfs에 대응 모듈과 의존성을 함께 포함한다. rootfs를 읽어야 rootfs 접근 드라이버를 로딩할 수 있는 순환 의존을 만들지 않는다.

rootfs 성공 경로에서는 pseudo filesystem mount를 새 root로 옮기고, boot log를 /run 아래 전달한다. 최종 systemd가 PID 1을 이어받아야 한다. 자식 프로세스로 systemd를 띄우고 /init이 남는 구조를 사용하지 않는다.

초기 read-only mount는 식별·검사를 위한 것이며 이것만으로 비정상 종료된 ext4의 모든 쓰기를 방지한다고 주장하지 않는다. journal replay 여부를 정책에 포함하고 손상 복구는 PC의 복제 이미지에서 수행한다.

## 실패 동작

SD 없음, 잘못된 UUID, filesystem 오류, marker 불일치, /sbin/init 누락, 필수 모듈 불일치는 진단 상태로 이동한다. timeout은 로그에 남기며 자동 포맷·내부 rootfs 대체·무한 재부팅을 하지 않는다.

개발용 진단 셸은 물리 USB 연결에서만 사용하고 일반 배포 프로필에서는 인증 정책을 적용하거나 비활성화한다. 네트워크로 무인증 root 셸을 열지 않는다.

자동 Android fallback이나 boot slot rollback은 v1 기능이 아니다. 실패 후 정상 boot로 돌아가는 경로는 recovery/Download Mode를 통한 명시적 복원이다.

## USB·pstore 진단

처음에는 USB ACM 포트가 PC에 나타나는지와 콘솔 입출력을 확인한다. 그다음 Windows와 실제 호환되는 USB network function을 검증해 SSH를 추가한다. NCM/ECM/RNDIS 중 이름만 보고 선택하지 않으며 host 지원·kernel function·device descriptor를 확인한다.

Gadget 설정은 configfs mount → function/config 구성 → UDC 연결 순서로 수행한다. 이미 바인딩된 Samsung gadget과 중복 구성하지 않는다. VID/PID·descriptor는 기준 이미지의 검증된 구성을 조사해 사용하며 임의의 다른 제품으로 가장하지 않는다.

ramoops 주소는 DT와 reserved-memory에서 확인한다. 겹치는 메모리를 추측해 예약하지 않는다. warm reset·recovery 진입·전원 차단의 로그 보존 차이를 시험한다. 아주 초기 실패에는 pstore가 남지 않을 수 있다.

## 부팅 단계별 관측점

| 단계 | 성공 증거 | 실패 시 우선 확인 |
| --- | --- | --- |
| bootloader 수용 | 커널 로그 또는 다음 단계 증거 | header·AVB·크기·DT |
| kernel 진입 | printk/pstore | DT·reserved memory·init 오류 |
| initramfs | 단계 표식·ACM 콘솔 | 압축·cpio·실행 권한·정적 ABI |
| SD 준비 | block 장치·UUID | clock·regulator·host·ext4 |
| rootfs 전환 | systemd PID 1 | loader·libc·mount·kernel config |
| 서비스 | SSH·journal | unit 의존성·네트워크·시간 |
| GUI | Xorg·Xfce 표시 | display API·permission·input |

## 완료 조건·산출물

정상 이미지 분석 보고서, 설명 가능한 재조립 차이, initramfs 로그, SD 실패 처리 기록, Debian PID 1 관측, 정상 이미지 복원 시험을 남긴다. 실제 합격 횟수와 회귀시험은 [검증 문서](11-validation-and-milestones.md)를 따른다.

## 참고

- [LineageOS 보드 설정](https://github.com/LineageOS/android_device_samsung_gta4l-common/blob/lineage-23.2/BoardConfigCommon.mk)
- [Ubuntu Touch deviceinfo](https://github.com/jojobear691/ubuntu-touch-samsung-gta4lwifi/blob/main/deviceinfo)
- [USB configfs](https://docs.kernel.org/usb/gadget_configfs.html)
- [ramoops](https://docs.kernel.org/admin-guide/ramoops.html)
