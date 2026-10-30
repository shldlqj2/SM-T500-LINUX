# 최신 인수인계 — Nura 26.06 기본 OS와 SM-T500 지원 선별 이식

## 갱신·전달 상태

- 갱신 날짜: 2026-10-30, Asia/Seoul. N2 결과·다음 실기기 조사와 삼성 펌웨어 제외 게시 검토 반영.
- 작성 주체: 현재 주 에이전트.
- 현재 단계: **N2 오프라인 준비 부분 완료**. 시험 DT·기기 APK를 빌드하고 공식 LTS 6.18.35-r0·모듈·표준 initramfs를 연결했다. `pmbootstrap install --no-image`와 383개 패키지의 저장소 신뢰 경로 검사는 종료 0. kernel 전체 로컬 컴파일·boot.img 생성·N2 ext4 rootfs 파일·실기기 검증은 미실행이다. 전체 DT binding의 upstream GPU 진단과 DT 선택·메모리/boot·SD 실패 정책이 남아 N2/M2 전체 합격은 아니다.
- 기록 상태: doctor/collect/report·basic/extended probe·collection JSON 계약 검사·설명 보고서 구현. 실기기 수집은 미실행이고 자체 sources/build CLI는 미구현이다. N1은 pmbootstrap 표준 도구로 실행했다.
- 이번 실행 범위: 이전 세션의 N2 산출물·로그를 읽기 전용으로 대조하고 누락된 APK 신뢰 경로 검증·산출물 복사·문서 갱신을 완료했다. [N2 실행 기록](docs/research/nura-n2-dt-2026-10-30.md)·D015를 따른다. 기기 접근·기록·재부팅·실제 SD 쓰기는 없었다. [N1](docs/research/nura-n1-rootfs-2026-10-30.md) 준비 이미지는 별도 세트로 보존한다.
- 후속 사용자 우선순위: 각 장치의 순정 driver·firmware·서비스 관계 분석을 먼저 진행한다. 이번 추가 조사는 내장 config와 동봉 vendor 파일 목록의 후보 대응까지 완료했으며 실제 vendor 모듈/HAL 내용 분석은 남아 있다.
- 최신 사용자 확정: **Nura 26.06 공식 기본 구성을 바탕으로 포팅하고 기존 Tab A7 postmarketOS에서는 필요한 기기 정보·코드만 가져온다. SM-T500은 Wi-Fi 전용이므로 LTE 설정을 도입하지 않는다.** [실행 계획](docs/14-nura-26.06-port-plan.md)·D014가 이전 Debian/제조사 kernel 우선 계획을 대체한다. 실제 Nura 설치·부팅은 아직 미실행이다.
- 버전 구분: 기존 Tab A7 prebuilt는 입력에 사용하지 않았다. N1/N2는 공식 v26.06·Alpine 3.24.3/aarch64·systemd 261이며 `os-release`는 `NAME=postmarketOS`, `VERSION_ID=v26.06`이다. N1 362개 패키지의 ext4 이미지와 N2 383개 패키지 트리를 구분한다. N1에는 N2 모듈이 없어 현재 kernel과 결합하지 않는다.
- 기록과 실물의 차이: 재개 당시 HANDOFF는 N1 상태였으나 N2 DT·install·검증 파일이 존재했다. 11개 산출물/APK·52개 DT 입력/출력 레코드 해시와 소스 사본을 대조해 일치를 확인했다. 과거 install 로그의 활성 chroot 안내와 달리 재개 시 N2 mount·관련 프로세스·ARM64 binfmt는 없었다. `private/nura/n2/resume-audit.json`을 따른다.
- 실제 소유권 이전: 요청 없음. 다른 에이전트 실행·메시지 전송·worktree 생성 없음.

## 최신 요청과 Git 게시 범위

- 사용자는 인수인계 작성·커밋을 요청했고 삼성 펌웨어를 자세히 확인해 문제가 있으면 제외하고 푸시하도록 명시했다. 현재 `master` → 기존 `origin/master`의 일반 푸시가 허용된 범위다. 기기 기록·다른 에이전트 실행은 요청하지 않았다.
- [게시 검토](docs/firmware/redistribution-review-2026-10-30.md)·D016에 따라 전체 삼성 펌웨어 재배포 권한을 확인하지 못해 바이너리를 제외한다. AP·CSC/HOME_CSC는 GitHub 일반 Git 100MiB 제한도 초과한다. 원본 파일은 삭제/이동하지 않고 로컬에 보존한다.
- 게시 대상은 이전부터 누적된 Nura 전환 문서·순정/기존 포트 분석 요약·N1/N2 실행 기록·`ports/` 소스·제외/개행 규칙이다. 펌웨어 원본과 `private/`·`artifacts/`·WSL 바이너리/로그·서명 개인 키·백업은 포함하지 않는다.
- 커밋 전 Git index는 비어 있었고 현재 추적 파일에 금지 경로/이미지·펌웨어 payload가 없음을 확인했다. staged 실제 내용·도달 가능한 Git 이력·비밀값/식별자·파일 크기/형식·문서 링크를 검사한 결과는 `private/publication/20261030/`에 보존한다. 커밋·푸시의 관측 결과는 게시 후 이 절에 갱신한다.
- 다음 작업의 첫 행동은 태블릿 USB 연결 후 ADB의 설치·인식·인증 가능 여부를 읽기 전용으로 확인하는 것이다. 모델·부트로더 리비전·파티션·실제 DT를 조사하고 아래 최대 3개 작업의 완료 조건을 따른다. ADB/root가 가능하다고 가정하지 않는다.

## 목표와 현재 요청 범위

사용자는 SM-T500에 네이티브 Nura 26.06을 포팅하며 kernel을 학습하려 한다. 최신 기준은 공식 v26.06/aarch64 rootfs, 호환되는 유지되는 mainline/LTS 후보, microSD ext4, systemd host PID 1, 터치 Xfce, Docker 웹/API 작업이다. 제한적 Android HAL은 허용하며 전체 기능과 One UI 재설치 경로를 유지한다. 기존 Tab A7 포트에서는 출처를 검증한 deviceinfo·DTS·driver/firmware·초기화 변경만 선별 이식한다.

이전 요청의 첫 구현 단계인 수집기와 합성 검증은 완료했다. D014 이후 이미지·패키지는 pmbootstrap/Nura 표준 도구를 사용하며 미구현 자체 sources/build 엔진과 BusyBox /init 전체를 먼저 구현하지 않는다. 기존 JSON collection v1과 코드에는 변경이 없다. 실기기 수집에는 ADB·연결·인증이 필요하고 PATH의 ADB는 앞선 조사에서 확인되지 않았다.

2026-10-30 사용자는 순정 One UI를 다시 설치해 포팅 기준으로 삼겠다고 했고 현재 폴더에 펌웨어를 제공했다. D013에 따라 LineageOS 설치 패키지·이미지 확보와 재설치는 필수 선행 조건에서 제외했다. **One UI 설치·복구가 완료된 상태는 아니다.** 순정 전환과 관련해서는 제공 파일의 정적 조사만 실행했다. 오프라인 N2 준비와 기기 전환을 구분하며 다음 기기 단계는 실제 리비전·백업·복구 관문을 확인한 뒤 진행한다.

이후 사용자는 장치별 순정 드라이버 분석의 중요성을 지적했다. docs/07에 따라 장치→DT→kernel driver→firmware/보정 자료→초기화 서비스→Nura API 관계부터 정리한다. One UI 재설치는 오프라인 분석·빌드의 선행 조건이 아니며, 실제 부품·DT 선택·bind·기능 확인은 이후 정상 기기 조사로 보완한다.

이전 비교에서 linked downstream config의 PID_NS·CGROUP_PIDS 비활성과 mainline config의 주요 컨테이너 옵션 활성화를 확인했다. 위키 기능표는 배포 이미지 보장표가 아니고 microSD 부팅도 계획으로 표기돼 있다. 현재는 해당 오래된 kernel/config·rootfs를 전체 계승하지 않으며 공식 Nura 26.06 기준에서 필요한 기기 지원만 재검증한다. 기존 포트의 source/prebuilt 대응 조사보다 새 공식 기반과 선별 이식이 우선이다.

이미 합의한 선택은 [결정 기록](docs/decisions.md)에 있다. 사용자에게 배포판·GUI·학습 경험·복구 범위를 다시 묻지 않는다.

## 저장소·환경

- Windows 경로: C:\Users\SSAFY\orca\projects\PlayGround\SM-T500-LINUX
- Shell: PowerShell.
- Branch: master.
- D014 전환 작업 시작 시 HEAD: `9800649`. 앞선 세션의 `.gitignore`·README·HANDOFF·docs 변경과 미추적 firmware/research 문서가 있었고 보존했다. 이번에는 AGENTS·아키텍처·개발/부팅/커널/GUI/검증 계획 등을 추가 갱신했으며 코드·개인 원본은 수정하지 않았다.
- N2 재개 시작 시 HEAD: `9800649c2682d587419159c778fd8d9f77435391`, `docs: record collector push in handoff`. `master...origin/master`이며 앞선 문서 변경·미추적 `.gitattributes`·firmware/research 문서·ports가 존재했고 보존했다. 펌웨어만 미추적이었던 과거 조사 시작 상태와 구분한다.
- 수집기 구현 작업 시작 시 HEAD: 61351399946b165e3a261d7c5b472b18cf4d2f37, `docs: record design push in handoff`.
- 설계 문서 commit: 7631e5a, `docs: specify collector and build artifact contracts`.
- 과거 수집기 작업 당시 문서: 해당 HEAD까지 origin/master 추적 ref와 일치했고 당시 시작 시 worktree는 깨끗했다. 현재 N1/N2 작업은 미커밋이다.
- 수집기 구현 commit: `36c02c7`, `feat: implement SM-T500 device collector`. 수집기·테스트·설계/안내 문서 23개 파일을 포함하며 `origin/master` 푸시를 완료했다.
- WSL2: Ubuntu-24.04, WSL kernel `6.18.33.2-microsoft-standard-WSL2`, Python 3.12.3, Git 2.43.0. N1 시작 시 Linux 파일시스템 여유 약 953GiB·메모리 약 15.5GiB를 확인했다. mount/chroot/binfmt·ARM64 사용자 공간은 N1에서 사용했으며 커널 컴파일·USB 전달은 미검증이다.
- N1 Linux 작업 공간: `/home/ssafy/sm-t500-nura/n1-20261030`. 기본 사용자의 sudo에는 암호가 필요해 WSL root와 pmbootstrap 공식 `--as-root`를 사용했다. sudoers·암호·전역 Git 설정은 바꾸지 않았다. `kpartx 0.9.4-5ubuntu8.2`만 호스트에 추가했고 패키지 업그레이드는 하지 않았다.
- N1 도구/소스: pmbootstrap `3.12.1`, commit `46ee403e4680002ce42dc2645adf9b08557270e9`; pmaports `v26.06`, commit `2a8621d64d91647f7362eac59e7cdc091ff2bba8`. pmaports의 로컬 변경은 새 `device-samsung-gta4lwifi` 초안뿐이다. systemd-v26.06 채널·console UI·aarch64로 준비했다.
- N2 Linux 작업 공간: `/home/ssafy/sm-t500-nura/n2-20261030`. 도구/소스 commit은 N1과 같고 별도 checkout이다. 로컬 pmaports 변경은 `device/testing/device-samsung-gta4lwifi/`와 `dtb-samsung-gta4lwifi/` 두 패키지다. DT 컴파일용 Linux 6.18+stable patch와 Kbuild/binding integration 변경은 별도 `sources/linux-6.18/`에 있다. 호스트 GCC 13.3.0·dtc 1.7.0·격리 dtschema 2026.9를 사용했다. kernel 전체 컴파일 환경 검증은 미실행이다.
- Python: Windows 3.12.10, WSL Ubuntu-24.04 3.12.3에서 합성 시험을 실행했다.
- ADB: 이번 doctor --scope collect 결과 tool_missing·종료 코드 3. 현재 PATH에서 찾지 못한 결과이며 PC 전체에 없다고 확정한 것은 아니다. 실기기 연결·root는 검사하지 않았다.
- 2026-10-30 재확인: PATH의 ADB·7z는 발견되지 않았고 Windows tar·Python·WSL은 발견했다. WSL의 기존 `liblz4.so.1`로 압축 해제를 실행했다. 실기기 연결·ADB 인증·root는 조사하지 않았다. REA MCP의 도구는 사용 가능하며 외부 엔진 없이 `inspect_devicetree`를 실행했다.

수집기 구현은 `36c02c7`로 커밋해 `master`에 기록하고 `origin/master`에 푸시했다. 당시 푸시 후 로컬 HEAD와 `origin/master`가 일치하고 worktree가 깨끗한 것을 확인했다. N2 검증 종료 시에는 정적 조사·문서·N1/N2 ports 변경이 미커밋이었다. 이후 사용자의 명시적 커밋·푸시 요청을 받았으며 최신 게시 상태는 위 절을 따른다. [전달 지침](docs/handoff/GUIDE.md)에 따라 실제 변경 파일을 전달한다.

## 기기 상태

| 항목 | 현재 알려진 상태 | 근거 |
| --- | --- | --- |
| 모델 | SM-T500 | 사용자 설명 |
| OS | 마지막 사용자 설명은 LineageOS, One UI 전환 계획 채택 | 현재 실기기 미관측, 이번 세션 전환 미실행 |
| 부트로더·root | 해제·루팅 상태 | 사용자 설명, 직접 검사 미실행 |
| microSD | 보유 | 사용자 설명, 용량·파일시스템 미확인 |
| 현재 USB 연결·boot 모드 | 미확인 | N2 재개 PC 조회에서 관련 이름의 PnP 장치·PATH의 ADB 발견 못함. 기기 상태 확정은 아님 |
| kernel/vendor/bootloader revision | 미확인 | 실기기 조사 미실행 |
| 마지막 기기 기록 | 없음 | 이번 작업에서 기기 변경 안 함 |
| 백업·복구 시험 | 미실행 | 계획만 있음 |
| 순정 파일 후보 | T500XXS8CXG1, AP·BL·CSC·HOME_CSC 정적 조사 완료 | 파일 무결성 확인, 기기 리비전·CSC 호환성·복원은 미검증 |
| 기기 변경 담당자 | 현재 진행 작업 없음 | 소유권 이전 없음 |

## 완료한 작업

| 작업 | 상태 | 근거·한계 |
| --- | --- | --- |
| 사용자 목표·선호 정리 | 완료 | docs/decisions.md; 일부 기술 값은 설계 기본값 |
| 공개 SM-T500 소스 조사 | 완료 | 각 기술 문서의 출처 링크; 실제 기기와 대응 미검증 |
| 주제별 상세 계획 | 작성 완료 | docs/01~13, 실기기 수행 결과가 아님 |
| 에이전트 지침·handoff 체계 | 작성 완료 | AGENTS.md, docs/handoff/GUIDE.md, TEMPLATE.md |
| 로컬 자료 제외 규칙 | 작성 완료 | .gitignore; 내용 검사를 대신하지 않음 |
| 기존 문서 정적 검사 | 검증 완료 | 이전 단계의 Markdown 19개·상대 링크 63개 검사 |
| 초기 문서 commit·push | 완료 | de4ad08, master → origin/master |
| 조사·빌드·데이터 계약 설계 | 작성 완료 | docs/design/01~03, 실제 CLI 코드 없음 |
| 새 설계 문서 정적 검사 | 검증 완료 | Markdown 22개·상대 링크 87개·JSON 예시 2개, 검사 문제 0건 |
| 설계 문서 commit·push | 완료 | 7631e5a, master → origin/master |
| 수집기 doctor/collect/report | 구현·합성 검증 완료 | tools/portctl.py, tools/portlib/, tools/README.md |
| 기본·확장 probe와 root 관문 | 구현·합성 검증 완료 | 정확한 식별 후 상세 읽기·필요 항목만 root 재시도 |
| collection v1 계약·원본 무결성 | 구현·합성 검증 완료 | strict reader/writer, 상태·참조·해시 검사 |
| Windows·Linux 동작 | 합성 검증 완료 | 아래 테스트 결과. 실제 ADB 및 태블릿 검증과 별개 |
| 실제 기기 수집 | 미실행 | ADB 설치·연결·인증 필요 |
| sources/build/artifacts CLI | 미구현 | docs/design/02·03 설계만 존재 |
| 제공 순정 패키지 정적 조사 | 검증 완료 | [조사 기록](docs/firmware/T500XXS8CXG1.md), 네 tar의 내장 MD5·SHA-256·선택 이미지 압축 해제·header·IKCONFIG 확인 |
| REA DT 조사 | 일부 엔트리 정적 파싱 완료 | base DTB 1개·DTBO 4개, 전체 트리 Evidence·요약 총 10개를 private에 내보냄. 실제 DT 선택·overlay 적용·기능은 미검증 |
| One UI 기준 ROM 선택 | 계획 채택 | D013. 기기 전환과 기준 기능·복구 검증은 미실행 |
| 순정 장치별 드라이버 후보 목록 | 일부 정적 조사 완료 | 내장 config와 FOTA vendor 파일 목록, `.ko` 경로 30개·여러 터치 firmware·HAL/rc 후보 확인. 실제 파일 내용·의존·실기기 bind는 미확인 |
| 기존 postmarketOS 포트 비교 | 정적 조사 완료 | 위키 원문·downstream/mainline 고정 commit 설정·recipe 17파일. Docker·SM-T500·microSD 부팅 실기기 검증은 미실행 |
| Nura 26.06 기본 OS 선택 | 계획·문서 반영 완료 | D014, docs/14. 공식 기반에서 SM-T500 지원만 선별 이식 |
| N1 도구·최소 device APK | 빌드·검사 완료 | pmbootstrap 3.12.1, 고정 v26.06 pmaports, `device-samsung-gta4lwifi 0.1-r0`. 커널·flash 설정이 없는 메타데이터 전용 초안 |
| N1 ARM64 rootfs 파일 | 생성·정적/사용자 공간 검사 완료 | 패키지 362개, QEMU로 aarch64/systemd 실행, ext4·압축·해시 검사. 전체 install은 커널 부재로 미완료이며 부팅 가능 이미지가 아님 |
| APK 저장소 신뢰 경로 | 오프라인 재검증 완료 | 설치된 362개를 서명된 index와 checksum 경로로 재설치해 종료 0. 캐시 465개 중 개별 APK 서명 단독 검사는 408개 통과·57개 UNTRUSTED로 구분 |
| N2 SM-T500 Wi-Fi DT·기기 APK | 빌드·부분 정적 검증 완료 | DTB 72,516 bytes, 호스트/APK 설치 산출물 해시 일치. 전체 schema에는 비교군과 같은 upstream GPU 진단 2개가 남음 |
| N2 공식 kernel·모듈·initramfs | 연결·무결성 검사 완료 | LTS 6.18.35-r0 APK, release/vermagic·최종 config·PHY 포함 검사. kernel 로컬 전체 빌드 아님 |
| N2 install·APK 신뢰 경로 | 검증 완료 | install·mkinitfs 종료 0. 383개를 새 트리에 오프라인·스크립트 비실행·allow-untrusted 없이 재설치해 종료 0 |
| N2 전체/M2·기기 부팅 | 부분 완료/미실행 | boot.img·대응 SD 파일·DT 선택/메모리·SD 실패 정책·기기/복구 관문이 남음 |

## 중요한 발견·미확인 사항

- 공개 LineageOS와 Ubuntu Touch의 ramdisk offset 표기가 다르다. 정상 boot.img 분석 전 어느 값을 채택하지 않는다.
- 제공 순정 boot/recovery header의 ramdisk 주소는 `0x02000000`, page는 4096, header는 v2다. 위 공개 설정의 차이와 구분해 이 이미지의 관측값으로 보존한다. 실기기 부트로더의 실제 배치는 미관측이다.
- 제공 순정 커널은 `4.19.157-perf-26272441-abT500XXS8CXG1`. 내장 IKCONFIG의 DEVTMPFS·PID_NS·CGROUP_PIDS·USER_NS·VT 비활성은 하드웨어/비교 자료이며 Nura 기준으로 상속하지 않는다. 공식 LTS 6.18.35-r0은 D015의 오프라인 평가 kernel이며 실기기 선택·지원 상태는 미검증이다.
- 공식 vmlinuz는 EFI zboot다. 소스 header와 대조해 ARM64 Image.gz/Image를 추출했지만 Samsung bootloader 수용·최종 배치는 미검증이다. 설치 config와 recipe의 활성 설정 차이는 `CONFIG_CC_CAN_LINK` 1개이며 producer commit이 `-dirty`라 정확한 source/바이너리 재현을 주장하지 않는다.
- SD L22/L5·카드 감지 GPIO 88·USB L4/L12/L15는 순정 Bengal 후보에서 얻은 연결 정보다. 실제 선택 DT·reserved-memory는 미확인이다. L7 always-on은 시험 가설이다. MPSS·IPA·셀룰러 서비스는 활성화하지 않았으며 Wi-Fi 공유 무선 의존성은 후속 조사한다.
- 동봉 FOTA 빌드 자료에서 system은 Android 12·One UI 속성 `40100`, vendor·boot header는 Android 11 표기다. `super`의 실제 논리 파티션 내용이나 설치된 기기의 버전을 확인한 결과는 아니다.
- boot DTB 11개·별도 DTBO 20개를 분리했다. Qualcomm 여러 보드 선언이 함께 있으며 실제 기기가 선택하는 조합은 미확인이다. 임의 첫 엔트리를 실기기 구성으로 확정하지 않는다.
- 공개 LineageOS source에는 cgroups·OverlayFS·seccomp·PSI·pstore 설정이 있으나 실제 최종 config와 런타임 동작은 미확인이다.
- 공개 터치 드라이버 설정으로 실물 터치 부품을 확정하지 않는다.
- 기존 Ubuntu Touch 포트는 Bluetooth를 실험 단계로 표시한다. 우리 Nura의 동작 증거가 아니다.
- 실제 모든 부팅·서비스·하드웨어·복구 시험은 미실행이다.
- 구현 기준은 docs/design/03-data-contracts.md의 JSON·상태·종료 코드다. 기기별 ready lock·recipe의 값은 아직 미확정이다.
- exec-out에는 원격 종료 frame이 없으므로 binary remote_exit_code는 null이며 형식 검사로 읽기를 판정한다. root adapter의 실제 ROM 호환성은 아직 미확인이다.
- 등록된 driver/sysfs 항목은 실제 하드웨어 사용 성공을 증명하지 않는다. 접근 불가·없는 선택 속성은 partial로 남을 수 있다.

## 진행 중 작업·산출물

- N1은 종료 시 `pmbootstrap shutdown`을 완료했다. N2의 과거 install 로그에는 활성 chroot 안내가 있으나 재개 읽기 전용 조회에서는 작업 mount·빌드 프로세스·qemu-aarch64 등록이 없었다. 이번에 중복 install·kernel 빌드·shutdown을 시작하지 않았다. Windows의 관련 PnP 장치·adb/odin/heimdall 프로세스·PATH의 adb는 발견하지 못했다. 기기의 현재 작업자는 미관측이며 기록 전 재확인이 필요하다.
- N2 산출물: `artifacts/nura-n2-20261030-stage-v1/`의 14개 파일. kernel/config/System.map·DTB·initramfs·Image/Image.gz·modules.tar.gz와 manifest·패키지/초기 archive 목록·audit·trust/provenance다. 크기·해시는 [N2 기록](docs/research/nura-n2-dt-2026-10-30.md)에 있다. Windows와 WSL `artifacts/stage-v1/` 사본 해시를 대조했다.
- N2 rootfs: 위 N2 Linux 작업 공간의 `work/chroot_rootfs_samsung-gta4lwifi/` 패키지 트리(383개, 약 746MiB). ext4 파일을 내보내지 않았고 N1 이미지로 대체하지 않는다. 전체 rootfs·상세 install 로그에는 생성용 로그인 설정이 있어 그대로 공개하지 않는다.
- N2 검증 증거: `private/nura/n2/`의 `stage-verification.json`·`manifest.json`·`resume-audit.json`·`repository-chain-result.json`·`delivery-result.json`·명령별 JSON. 상세 로그는 N2 WSL `logs/`와 `work/log.txt`다. trust 검증용 별도 `repository-validation-root/`는 오프라인·스크립트 비실행 설치 결과이며 부팅용 rootfs가 아니다.
- N2 마무리 검사: 2026-10-30T16:17:00+09:00, Windows PowerShell/Python·저장소 루트에서 Markdown 30개·상대 링크 166개·문자/fence/공백·로컬 source SHA-512·산출물 복사본/입력 해시·공유용 N2 문서 내용·패키지 shell/Python 구문·`git diff --check`를 검사해 문제 0건·종료 0. WSL 읽기 전용 조회에서도 작업 mount·관련 프로세스·ARM64 binfmt 없음. 요약은 `private/nura/n2/final-validation.json`이다. 수집기 suite·kernel 전체 빌드·실기기 시험은 실행하지 않았다.
- 사용자 제공 원본: 저장소 루트 `SAMFW.COM_SM-T500_XAR_T500XXS8CXG1_fac/`. 원본 변경·이동 없음. `.gitignore`에 이 폴더를 추가해 안내 txt까지 제외했다.
- 분석 자료: `private/firmware/T500XXS8CXG1/`의 `package-inventory.json`, `image-analysis.json`, `fota-metadata-inventory.json`, `rea-evidence.json`, 조사 스크립트·compressed/images/parts/fota-metadata 디렉터리. 전체 콘솔 로그는 별도 보관하지 않았고 세션 도구 출력에 있다. 구체 명령·환경·결과는 [조사 기록](docs/firmware/T500XXS8CXG1.md)을 따른다.
- 초기 패키지 조사 검증 결과: Markdown 24개·상대 링크 106개·추출 자료 레코드 58개(일부 동일 파일 중복 참조)의 크기/SHA-256 대조에서 문제 0건. `git diff --check` 통과. 실행 환경은 Windows PowerShell/Python, cwd는 저장소 루트, 종료 코드 0이며 요약은 `private/firmware/T500XXS8CXG1/validation.json`에 있다. 빌드·실기기 시험은 수행하지 않았다.
- N1 최종 산출물: `artifacts/nura-n1-20261030-final/nura-v26.06-samsung-gta4lwifi-n1-rootfs-only.img.gz`와 `manifest.json`. ext4 파일은 1,073,741,824 bytes·SHA-256 `6ad43a8471ee77e98d930d8c46dbbfb2047c4034f3a38052b8fc98e9578d4e5f`, gzip은 193,580,662 bytes·SHA-256 `219551a03244f72618fc65cbc7c64fe914d79a842a0db57c67de26026a4eb613`이다. kernel·DT·initramfs·boot는 없다. 이전 `artifacts/nura-n1-20261030/` 스냅샷은 폐기 대상 참고 자료이며 입력으로 사용하지 않는다.
- N1 공개 변경: `.gitattributes`로 APKBUILD/deviceinfo의 LF를 고정하고 `ports/device-samsung-gta4lwifi/` 초안을 추가했다. `deviceinfo_flash_method=none`, `deviceinfo_generate_bootimg=false`로 rootfs 준비 범위를 명시했다. 도구 구현의 v1 이미지 계약이나 완성된 포트로 취급하지 않는다.
- N1 실행 자료: `private/nura/n1/`의 작업 스크립트·명령별 결과 JSON·`rootfs-result.json`·`repository-chain-result.json`·`apk-signature-result.json`·`image-verification.json`. 상세 로그는 위 Linux 작업 공간의 `logs/`와 `work/log.txt`에 있다. 초기 `-l` 로그 경로에는 파일이 생기지 않아 후속 명령부터 실제 `work/log.txt`를 명령별로 복사했다. 원본에는 생성용 계정 정보가 있어 그대로 공개하지 않는다.
- N1 마무리 검사: 2026-10-30T15:33:53+09:00, Windows PowerShell/Python·저장소 루트에서 Markdown 28개·상대 링크 148개·문자/fence/후행 공백·deviceinfo SHA-512·최종 gzip SHA-256·manifest 사본 일치와 `git diff --check`를 검사해 문제 0건·종료 0을 확인했다. WSL root 읽기 전용 조회에서 작업 공간 mount·빌드 프로세스·qemu-aarch64 binfmt 등록이 없었다. 요약은 `private/nura/n1/final-validation.json`이다. 실기기·Docker 시험은 실행하지 않았다.
- Nura 기준 증거: `private/research/nura-26.06-baseline/`의 `upstream-observations.json`, 공식 base/pmaports.cfg·generic kernel recipe. pmbootstrap 요구 최소는 3.11.0이고 N1 선택 도구는 위에 기록한 3.12.1이다. 초기 조사 뒤 실제 준비가 진행된 차이를 N1 기록에 반영했다.
- D014 문서/입력 검사: Windows PowerShell/Python·저장소 루트에서 Markdown 26개·상대 링크 139개·원본 upstream 파일 5개의 크기/SHA-256을 검사해 문제 0건·종료 0을 확인했다. 최종 문서 조정 후 링크·문자·fence 및 `git diff --check`도 통과했다. 요약은 위 디렉터리의 `validation.json`에 있다. 코드 테스트·실기기 시험은 이번 문서 작업 범위 밖이다.
- 추가 드라이버 증거: 같은 private 디렉터리의 `inspect_driver_inventory.py`, `driver-inventory.json`, `driver-inventory/vendor_filesystem_config.txt`. Windows Python·저장소 루트에서 실행, 종료 0. 모듈 바이트를 읽은 결과가 아닌 동봉 파일 목록의 후보 분류다.
- postmarketOS 검토 증거: `private/research/postmarketos-20261030/`의 위키 원문 JSON·GitHub 브랜치/tree·고정 소스 파일·source-manifest. downstream `35b3893a62ea326fe487b0790827fc1a72717f49`, mainline `d7fa5a483d488c11a7b4b589b9cc0fda1ed4cf0c`. 위키 kernel 7.2.0과 linked mainline recipe 6.10의 불일치는 미해결이며 배포 이미지와의 대응 확인 필요. 자세한 실행 결과는 검토 문서를 따른다.
- postmarketOS 비교 검증: 2026-10-30T14:24:43+09:00, Windows Python·저장소 루트에서 Markdown 25개·상대 링크 109개·소스 파일 17개의 크기/SHA-256 대조, 문제 0건·종료 0. `git diff --check` 통과. 요약은 같은 연구 자료 디렉터리의 `validation.json`에 있다. 관련 없는 코드 테스트·빌드·실기기 시험은 수행하지 않았다.
- 추가 드라이버 조사 검증: Markdown 24개·상대 링크 108개·후보 목록 입력 파일 두 개의 SHA-256 대조에서 문제 0건, `git diff --check` 통과. Windows Python·저장소 루트에서 실행, 종료 0. 요약은 `private/firmware/T500XXS8CXG1/driver-validation.json`에 있다.
- 개인 백업·EFS·원본 기기 덤프: 수집하지 않음.
- 정상 복귀 세트: 파일 후보는 확보했으나 실기기 호환성·재설치·정상 부팅·복원은 미검증. docs/03 관문 미통과.
- 인수인계 이력: 실제 이전이 없어 history snapshot을 만들지 않음.
- 합성 원본·로그·보고서: 테스트 임시 디렉터리에서 생성 후 정리했다. 실기기 증거를 생성하지 않았다. 테스트 콘솔 결과는 이 세션의 도구 출력이며 별도 상주 원본 로그 파일은 보관하지 않았다.

## 다음 작업: 최대 3개

1. 실제 DT 선택·메모리 예약·boot 계약 확정.
   - 순정 후보와 실기기 정보를 대조하고 header·AVB·DTB/DTBO·최종 배치/크기 계약을 확정한다. upstream GPU binding 진단과 정확한 kernel source 재현 필요도 추적한다.
   - 완료 조건: 추측 없는 대상 DT·reserved-memory·배치·크기 대조표. 단순 schema 종료 0이나 버전 일치를 합격으로 해석하지 않는다.
2. N2 대응 SD rootfs·표준 initramfs 정책 확정.
   - N2 트리의 모듈/패키지 세트를 보존해 SD UUID/실패 처리와 USB 진단 경로를 조사한다. N1 rootfs를 현재 kernel과 결합하지 않는다.
   - 완료 조건: 대응 rootfs 이미지·UUID/해시·initramfs 설정/모듈 목록 및 SD 없음/오류 시 내부 저장소로 전환하지 않는 오프라인 검사.
3. 실기기 조사·복구 관문 후 첫 Nura 부팅.
   - docs/02·03에 따라 모델·리비전·파티션·부품·백업·기록 담당자와 One UI 정상/복구 기준을 확인한다.
   - 완료 조건: 복구 증거와 실제 SD rootfs·kernel/initramfs/systemd 단계별 로그. 내부 rootfs 설치·부트로더/PIT 변경을 수행하지 않는다.

## 반복 금지·주의

- 계획 문서의 체크리스트를 실기기 검증 완료로 해석하지 않는다.
- Git HEAD와 수집기 코드는 존재한다. 아직 없는 빌드 CLI·기기 이미지·백업 경로를 존재한다고 쓰지 않는다.
- boot offset·block 번호·펌웨어를 추측해 기록하지 않는다.
- 문서 작성 요청만으로 새 에이전트·Orca worktree를 시작하지 않는다.
- 복구가 미검증이므로 커스텀 Linux 이미지 기록부터 시작하지 않는다.

## 이전 문서 검증 기록

- 실행 시각: 2026-09-29T14:06:39+09:00.
- 환경·cwd: Windows PowerShell, 위 저장소 경로.
- 검사: Get-ChildItem으로 Markdown을 수집하고 UTF-8로 읽어 상대 링크의 Test-Path, 코드 fence 짝, 대체 문자, 후행 공백을 검사했다.
- 결과: Markdown 19개, 상대 링크 63개, 검사 문제 0건, 명령 종료 코드 0.
- 내용 점검: Debian·커널·GUI 선택, 복구 관문, E0~E6, 미실행 시험 표기, HAL의 host/container PID 구분, 미커밋 전달 조건을 대조했다.
- 한계: 외부 URL 전체의 가용성 검사, Markdown 렌더링 시각 검사, 커널 빌드·실기기 시험은 수행하지 않았다.
- 당시 Git 상태는 첫 commit 전이었다. 이후 사용자 요청으로 de4ad08 commit·push를 완료했다.

## 이번 설계 문서 검증

- 실행 시각: 2026-09-29T17:05:02+09:00.
- 환경·cwd: Windows PowerShell, 위 저장소 경로.
- 검사: rg --files로 Markdown을 열거하고 UTF-8로 읽어 상대 링크 존재, 코드 fence 짝, 대체 문자, 후행 공백, JSON 예시의 ConvertFrom-Json 문법 검사를 수행했다.
- 결과: Markdown 22개, 상대 링크 87개, JSON 예시 2개, 검사 문제 0건, 명령 종료 코드 0.
- Git 검사: git diff --check 통과. LF→CRLF 안내는 있었으나 공백 오류는 없었다. 정적 검증 당시 HEAD와 origin/master는 de4ad08로 일치했다. 이후 사용자 요청으로 `git push origin master`를 실행했고 종료 코드 0, `de4ad08..7631e5a master -> master`를 확인했다.
- 계약 대조: CLI의 미구현 표기, source lock의 draft/ready 경계, 수집 partial·중단 상태, 개인정보 공유 제한, bundle 필수 role과 FileDigest 필드 정의를 점검했다.
- 수정: 모듈이 없는 bundle도 build-metadata를 갖도록 명시하고 manifest·최종 build-run 사이의 순환 참조를 피하도록 정리했다.
- 한계: JSON 문법 확인은 계약 validator 시험이 아니다. 외부 링크 가용성·렌더링·도구 코드·실제 빌드·실기기 시험은 검증하지 않았다.

## 2026-09-30 수집기 구현 검증

실행 환경·cwd: Windows PowerShell/Python 3.12.10, 위 저장소 루트. WSL은 Ubuntu-24.04/Python 3.12.3, /mnt/c/Users/SSAFY/orca/projects/PlayGround/SM-T500-LINUX. 커널 빌드를 수행한 것은 아니다.

| 검사 | Windows | WSL/Linux |
| --- | --- | --- |
| python -m unittest discover -s tests -v | 35개 중 28 통과·POSIX 7 skip, 종료 0 | 35개 모두 통과, 종료 0 |
| 식별 이전 root 차단·schema·CLI UTF-8·root 재시도·보고서 추가 검사 | 관련 5개 통과, 종료 0 | 관련 5개 통과, 종료 0 |
| 경로 확인 후 basic·보고서 불변·symlink 차단 검사 | 2 통과·POSIX 1 skip, 종료 0 | 3개 통과, 종료 0 |
| client 오류의 원격 exit 미확인·연결 해제·필수 kernel 실패 검사 | 관련 3개 통과, 종료 0 | 관련 3개 통과, 종료 0 |
| 실제 환경 doctor --scope collect | tool_missing, 종료 3 | 실제 ADB doctor는 실행하지 않음 |

후속 추가 검사는 tests/ cwd에서 python -m unittest -v <test_collector의 해당 case>로 실행했다. 현재 테스트 정의는 38개이고, 위 표는 기본 35개 실행 후 수정·추가한 항목을 선택 검증한 기록이다. 전체 suite를 마지막 수정 이후 다시 실행했다고 주장하지 않는다.

검증 범위: 대상 없음·복수·권한·상태·모델·코드명·프로토콜 관문, root 요청 제한, 빈 모듈, 실패 원본 보존, gzip CRC·부분 데이터·압축 해제 상한, DT cell·NUL, UTF-8 외 원본, stdout/stderr 동시 출력, 항목·전체 용량 한도, timeout·연결 해제·중단, 계약·원본 해시, 공유 보고서 식별자 차단, 기존 run/report 불변, workspace 잠금, 고정 shell script 문법·합성 파일 실행.

수정한 시험 문제: 첫 Windows 실행에서 문자열 'su' 검색이 power_supply를 root 호출로 오인했다. 실제 shell 명령/exec-out 실행 파일을 검사하도록 수정한 뒤 관련 시험이 통과했다.

한계: Windows의 실제 Ctrl+C 전달과 NTFS junction 시험, 실제 ADB client·ROM su·SELinux 정책·태블릿 probe는 미검증이다. 합성 shell 시험은 임시 트리에 대해 수행했다. 원본·보고서는 테스트 fixture이며 하드웨어 동작 결과가 아니다.

최종 문서·Git 검사: Markdown 23개·상대 링크 92개·JSON 예시 2개, 문제 0건. 신규 Python 파일 15개의 대체 문자·후행 공백 문제 0건. git diff --check 통과. 정적 검사 기준 HEAD는 6135139이며, 검증 후 `36c02c7`을 커밋·푸시했다. 푸시 확인 시점에는 HEAD와 origin/master가 모두 `36c02c7ab92e0f86b5e54beb9101d0dac2531743`이고 worktree는 깨끗했다. 문서 검사는 같은 PowerShell cwd에서 UTF-8 읽기·링크 Test-Path·JSON ConvertFrom-Json 방식으로 수행했다.
