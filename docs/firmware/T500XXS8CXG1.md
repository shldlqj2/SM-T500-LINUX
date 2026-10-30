# 제공 순정 패키지 T500XXS8CXG1 정적 조사

## 상태와 범위

최신 OS 기준은 [D014의 Nura 26.06 포팅](../14-nura-26.06-port-plan.md)이다. 아래는 제공 순정 파일의 실제 정적 조사 기록으로 보존한다. 순정은 하드웨어 관측·firmware·복구 자료로 쓰며 기존 4.19 config·kernel을 Nura 기본값으로 상속하지 않는다.

2026-10-30, Windows PowerShell/Python 3.12.10 및 WSL Ubuntu-24.04/Python 3.12.3에서 사용자가 제공한 파일을 조사했다. cwd는 이 저장소 루트다. 기기 접근·재부팅·플래싱·커널 빌드·이미지 재조립은 수행하지 않았다.

사용자는 순정 One UI를 다시 설치한 뒤 이를 포팅 기준으로 사용하기로 했다. [D013](../decisions.md)에 따라 LineageOS 패키지 확보는 필수 조건에서 제외한다. **제공 파일의 정적 조사 완료와 실제 기기의 One UI 정상 부팅·복구 검증은 별개다.**

원본은 저장소 루트의 `SAMFW.COM_SM-T500_XAR_T500XXS8CXG1_fac/`에 있으며 변경하지 않았다. 추출물·원본 설정·REA Evidence·조사 스크립트는 같은 PC의 `private/firmware/T500XXS8CXG1/`에 있다. 모두 Git 제외 대상이다. 공개 문서에는 패키지 메타데이터와 해시만 기록한다.

2026-10-30 [게시 검토](redistribution-review-2026-10-30.md)에서 전체 펌웨어의 재배포 권한을 확인하지 못해 원본·추출 바이너리를 푸시 대상에서 제외했다. 이 문서는 payload를 포함하지 않는 분석 요약이다.

## 파일 무결성과 구성

| 파일 구분 | 바이트 | SHA-256 |
| --- | ---: | --- |
| AP | 5,397,688,445 | `f27b202c33fabff61303a39502574f5363e577d8fb1372180b308bb1f141f2aa` |
| BL | 36,761,710 | `d767455901c8fba6624587f4413a6921b312b0a163077bafce591b2bdfa2775f` |
| CSC | 181,483,622 | `9aaf7b7ab06a5d3759b54578685f932af283b870bc059bc8d41267981ad00a7f` |
| HOME_CSC | 181,463,147 | `594d87a02bc2d16a64adead25ff7c27a70129f928ef6f8f7bc57d208a6083040` |

네 `.tar.md5` 파일 모두 끝에 포함된 MD5와 그 앞 tar 바이트의 계산 결과가 일치했다. 이는 패키지 내부 무결성 검사이며 Samsung의 별도 신뢰된 배포 해시·서명으로 출처를 검증한 결과는 아니다. 폴더의 XAR와 패키지의 OXM 표기는 관측했지만 실제 기기 CSC·호환성·롤백 제한은 미확인이다.

- AP: `boot.img.lz4`, `recovery.img.lz4`, `dtbo.img.lz4`, `super.img.lz4`, `userdata.img.lz4`, `metadata.img.lz4`, `vbmeta.img.lz4`, `vbmeta_samsung.img.lz4`, `modem.bin.lz4`, `meta-data/fota.zip`.
- BL: 부트로더·보안·DSP 관련 payload와 `NON-HLOS.bin.lz4` 등을 포함한다. 이번에는 목록만 읽었으며 실행·기록하지 않았다.
- CSC: `GTA4LWIFI_EUR_OPEN.pit`와 지역 관련 이미지 등을 포함한다. PIT 내용 분석·기기 파티션 매핑·재파티셔닝은 수행하지 않았다.
- HOME_CSC: 지역 관련 이미지·download-list 등을 포함한다. 선택에 따른 실제 데이터 보존 여부는 이번 조사로 검증하지 않았다.

## Android와 vendor 버전

AP 내부 `meta-data/fota.zip`의 빌드 메타데이터를 읽었다. `super`의 실제 논리 파티션은 아직 풀지 않았으므로 아래는 **동봉 빌드 자료의 선언값**이다.

| 자료 | 관측값 |
| --- | --- |
| `SYSTEM/build.prop` | `ro.build.PDA=T500XXS8CXG1`, Android `12`, SDK `31`, `ro.build.version.oneui=40100` |
| system 보안 패치 | `2024-06-01` |
| `VENDOR/build.prop` | Android `11`, `samsung/gta4lwifixx/gta4lwifi:11/RP1A.200720.012/T500XXS8CXG1:user/release-keys` |
| `META/misc_info.txt` | `os_version=12`와 `mkbootimg_version_args=--os_version 11 --os_patch_level 2024-06-01`을 함께 선언 |
| 동적 파티션 선언 | `system odm product vendor`, super 크기 `5729419264` 바이트 |

따라서 boot header의 Android 11 표기를 패키지 전체가 Android 11이라는 뜻으로 해석하지 않는다. system의 Android 12와 vendor/boot의 Android 11 표기를 각각 보존한다. 메타데이터의 super 크기를 실측 기기 크기로 사용하지 않는다.

## 부팅 이미지 관측

WSL에 이미 있는 `liblz4.so.1`을 사용해 boot·recovery·DTBO·두 vbmeta 파일만 압축 해제했다. 원본 압축 파일과 해제한 파일의 해시를 구분해 보존했다.

| 항목 | `boot.img` | `recovery.img` |
| --- | --- | --- |
| 이미지 바이트 | 100,663,296 | 103,546,880 |
| SHA-256 | `fffd5bdc89df24ab5d794ed88f2d697c79b71beb2e3711651d91e9416768defb` | `4a92383b867d6dcd89eb47e3851a55a7cf819ebff17cfee486f672916594e80c` |
| header / page | v2 / 4096 | v2 / 4096 |
| kernel 크기 | 15,788,241 | 15,788,241 |
| ramdisk 크기 | 803,687 | 8,484,010 |
| header의 ramdisk 주소 | `0x02000000` | `0x02000000` |
| header의 DTB 주소 | `0x01f00000` | `0x01f00000` |
| DTB 영역 바이트 | 3,124,694 | 3,124,694 |
| EOF AVB footer magic | 있음 | 있음 |

kernel banner는 `4.19.157-perf-26272441-abT500XXS8CXG1`, 빌드 시각은 2024-07-04 KST, 컴파일러 표기는 Android NDK clang 10.0.7이다. 이 문자열만으로 정확한 컴파일러 배포물·소스 SHA가 확정되지는 않는다.

이미지의 header·gzip 스트림·내장 IKCONFIG를 정적으로 읽었다. 추출한 boot/recovery 설정의 SHA-256은 모두 `83b84d030907ffb7a809aa5e057428b39734b42740874ace3a4ee52283e8da86`이다. AVB footer magic 확인은 서명 검증·부트로더 수용 시험이 아니다. header 주소는 이미지에 적힌 값이며 실행 시 실제 메모리 배치를 관측한 것이 아니다.

설정에서 `BLK_DEV_INITRD`, `MMC_SDHCI_MSM`, `EXT4_FS`, `CGROUPS`, `MEMCG`, `OVERLAY_FS`, `SECCOMP_FILTER`, `PSTORE_RAM`, `USB_CONFIGFS_ACM`, `INPUT_EVDEV`는 `y`다. `DEVTMPFS`, `CGROUP_PIDS`, `PID_NS`, `USER_NS`, `VT`는 비활성화되어 있다. `CONFIG_CMDLINE`은 `cgroup_disable=pressure`다. 일반 Linux/Docker의 요구사항 비교 자료이며 D014의 Nura용 kernel 최종 설정·런타임은 별도로 검증한다.

boot header의 cmdline에는 `firmware_class.path=/vendor/firmware_mnt/image`가 있다. 이후 실제 firmware 파일·마운트·서비스 의존성을 조사할 단서이며 Nura의 firmware 경로는 선택한 driver와 표준 패키지에 맞춰 별도로 확인한다.

## REA 조사

boot의 DTB 영역에서 FDT 11개, 별도 DTBO 테이블에서 엔트리 20개를 분리하고 해시를 기록했다. REA `inspect_devicetree`로 `boot-dtb-000.dtb` 및 DTBO 인덱스 0·13·14·19를 조사했다. 전체 DT/overlay 조합을 검증한 것은 아니다.

첫 base DT는 Bengal SoC 선언과 `sdhc1`·`sdhc2` alias를 포함한다. 조사한 overlay에는 Bengal·Khaje·Scuba 등 여러 Qualcomm 보드 선언이 있다. **기기에서 실제 선택되는 base DT·overlay·터치 부품은 미확정**이다. 임의로 첫 엔트리나 가장 큰 엔트리를 실기기 DT로 선택하지 않는다.

REA는 FDT 구조·속성을 파싱했으며 overlay 적용·binding별 참조·실제 전원/드라이버 동작은 검증하지 않았다. 일부 `reg` 속성의 파생 해석 제한과 미해결 참조는 원본 Evidence에 남겼다. 정적 전체 분석 기록 5개와 요약 view 5개를 `rea-evidence.json`으로 내보냈다.

## 명령·증거와 다음 단계

2026-10-30 추가로 `python private/firmware/T500XXS8CXG1/inspect_driver_inventory.py`를 Windows/Python·저장소 루트에서 실행했다(종료 0). FOTA의 `META/vendor_filesystem_config.txt`를 별도로 보관하고 내장 config와 함께 드라이버 조사 후보를 만들었다. 원본 목록 SHA-256은 `6dcb249e3e9a1ca14fef12a59c7cb6196f4586519ec63e01aaecf079a57ab72c`이며 결과는 `driver-inventory.json`, 원본은 `driver-inventory/vendor_filesystem_config.txt`에 있다.

모듈 경로 30개에 `qca_cld3_wlan.ko`와 `audio_machine_bengal.ko`·`audio_adsp_loader.ko` 등이 선언돼 있다. 터치 firmware 경로에는 Himax·FocalTech·Novatek 계열이 함께 있으며 config에도 여러 터치 드라이버가 켜져 있다. `CONFIG_QCOM_KGSL=y`도 확인했다. 이 자료는 [장치별 분석](../07-hardware-enablement.md)의 출발점이며 실제 vendor payload의 파일 내용·DT 선택·드라이버 bind를 확인한 결과가 아니다. 후보 이름을 정규식으로 분류한 항목은 확정 의존성이 아니다.

| 실행 환경·명령 | 결과 | 로그·증거 위치 (`private/firmware/T500XXS8CXG1/` 기준) |
| --- | --- | --- |
| Windows `python private/firmware/T500XXS8CXG1/inspect_package.py` | 종료 0, tar 목록·해시·내장 MD5 확인 | `package-inventory.json`, `compressed/` |
| WSL `python3 private/firmware/T500XXS8CXG1/inspect_images.py` | 종료 0, 선택 이미지 압축 해제·header/config/DT 분리 | `image-analysis.json`, `images/`, `parts/` |
| Windows Python `tarfile`/`zipfile`로 FOTA의 작은 메타데이터 선택 읽기 | 종료 0, 빌드 선언값 확보 | `fota-metadata/`, `fota-metadata-inventory.json` |
| REA `inspect_devicetree` / `export_evidence_bundle` | 정적 분석 5개, Evidence 10개 내보내기 완료 | `rea-evidence.json` |

WSL 초기 명령 탐색은 PowerShell과 중첩 shell의 인용부호 처리 때문에 실패했다. 이후 실제 분석은 WSL Python 스크립트 파일을 직접 실행해 성공했다. 추가 패키지 설치나 REA 설정 변경은 하지 않았다. 스크립트는 이번 로컬 조사 자료이며 `portctl`의 구현된 CLI가 아니다. 콘솔 실행 기록은 세션 도구 출력이며 별도 전체 콘솔 로그는 보관하지 않았다.

종료 전 Markdown 24개·상대 링크 106개·추출 자료 레코드 58개의 파일 크기/SHA-256을 검사해 문제 0건을 확인했다. 레코드 수에는 같은 config·DT를 중복 참조한 항목이 포함된다. `git diff --check`는 통과했고 정적 검사 요약은 `validation.json`에 보관했다.

1. 장치별 드라이버·firmware·서비스 대응 관계를 정적으로 조사한다. 완료 조건: 실제 vendor payload·대응 소스·DT를 확인하고 장치별 재사용/재빌드/서비스 대체/HAL 후보와 미확인 사항 기록.
2. 기기의 모델·CSC·bootloader 리비전과 개인/고유 데이터 백업 조건을 확인한다. 완료 조건: [복구 지침](../03-backup-and-recovery.md)의 실제 대상·롤백·백업 관문 충족.
3. One UI 재설치와 기준 조사로 정적 분석을 검증한다. 완료 조건: 정상 부팅·핵심 기능·Download Mode 복귀를 관측하고 실제 선택 DT·bind된 드라이버·firmware·서비스를 이미지 자료와 연결.

header 해석 기준은 [AOSP bootimg.h](https://android.googlesource.com/platform/system/tools/mkbootimg/+/refs/heads/main/include/bootimg/bootimg.h), DTBO 테이블 기준은 [AOSP dt_table.h](https://android.googlesource.com/platform/system/libufdt/+/refs/heads/main/utils/src/dt_table.h)다. 저장소의 실제 이미지 계약은 [docs/05](../05-boot-and-image-design.md)를 따른다.
