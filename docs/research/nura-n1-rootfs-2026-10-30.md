# N1 실행 기록 — Nura 26.06 ARM64 rootfs 준비

## 결과와 검증 범위

2026-10-30 [포팅 계획 N1](../14-nura-26.06-port-plan.md)을 실행해 공식 패키지 기반 **rootfs 준비물**을 생성했다. SM-T500용 최소 메타데이터 패키지를 빌드했고 v26.06·Alpine 3.24.3·aarch64·systemd 261을 확인했다. ext4 파일 이미지 생성·검사와 압축 왕복 검사를 완료했다.

**전체 pmbootstrap install은 완료되지 않았다.** 패키지 설치 후 kernel/flavor가 없어 mkinitfs에서 종료 1로 멈췄다. 설치된 패키지 트리를 검사하고 준비용 rootfs 이미지로 별도 저장했다. kernel·DT·firmware·initramfs·boot.img는 없으며 태블릿 부팅·systemd PID 1·Docker·하드웨어 동작·One UI 복구는 미검증이다. N1 사용자 공간 준비와 N2/N3 부팅 세트를 구분한다.

## 환경·입력

| 항목 | 관측값 |
| --- | --- |
| 실행 환경 | Windows PowerShell → WSL Ubuntu-24.04, Linux ext4 파일시스템 |
| WSL kernel | `6.18.33.2-microsoft-standard-WSL2`, x86_64 |
| WSL Python / Git | 3.12.3 / 2.43.0 |
| 메모리 / Linux 여유 디스크 | 약 15.5GiB / 953GiB (시작 시 관측) |
| 독립 작업 디렉터리 | WSL 사용자 홈의 `sm-t500-nura/n1-20261030/` |
| pmbootstrap | 3.12.1, `46ee403e4680002ce42dc2645adf9b08557270e9` |
| pmaports | v26.06, `2a8621d64d91647f7362eac59e7cdc091ff2bba8` |
| 실제 채널 | `systemd-v26.06`, pmaports v26.06 |
| 기기 패키지 | [device-samsung-gta4lwifi](../../ports/device-samsung-gta4lwifi/README.md), 0.1-r0, 메타데이터만 포함 |
| 호스트에 추가한 도구 | Ubuntu `kpartx` 0.9.4-5ubuntu8.2 하나. 다른 패키지 upgrade/remove 없음 |

일반 사용자의 sudo는 비밀번호가 필요했으므로 비밀번호·sudoers를 변경하지 않고 WSL root 호출과 pmbootstrap의 공식 `--as-root` 옵션을 사용했다. 새 독립 작업 디렉터리에 한정하며 system-wide Git 신뢰 설정 대신 프로세스 환경의 `safe.directory`에 해당 두 소스 경로만 지정했다.

pmaports의 선택 commit은 유지했다. pmbootstrap이 채널 목록을 `origin/main`에서 읽으므로 그 ref를 추가로 읽었지만 package checkout·APK 채널을 edge로 변경하지 않았다. 해당 ref SHA는 비공개 manifest의 `channels_catalog_commit`에 기록했다. 기본 계정·키·기기 식별자는 공유 문서에 기록하지 않는다.

## 실제 rootfs 내용

| 항목 | 결과 |
| --- | --- |
| os-release | `ID=postmarketos`, `VERSION_ID=v26.06` — 공식 패키지의 기존 명칭 유지 |
| Alpine | 3.24.3 |
| 아키텍처 | `apk --print-arch`가 aarch64, systemd ELF64 little-endian·e_machine 183 |
| systemd | 261-r0, ARM64 chroot에서 `systemd --version` 실행 성공 |
| base / base-systemd | 62-r0 / 77-r0 |
| 설치된 패키지 | 362개. Nura console UI가 선택한 기본 provider도 포함 |
| init | `../lib/systemd/systemd` 링크 |
| 로그인·SSH | N1 계정 잠금, sshd 기본 시작 비활성. 실제 로그인 시험은 하지 않음 |

저장소는 Nura v26.06·systemd v26.06 및 Alpine v3.24 main/community의 HTTPS 경로다. 독립 이미지에는 `/mnt/pmbootstrap/packages/` 빌드 전용 경로를 제거하고 공식·로컬 메타데이터 패키지의 공개 검증 키만 보존했다. 개인 SSH 키나 기존 기기 자료를 rootfs에 복사하지 않았다.

## 산출물

최종 파일은 저장소 루트의 Git 제외 경로 `artifacts/nura-n1-20261030-final/`에 있다. WSL의 `artifacts-final/`에도 원본을 보존했다. 실제 접근 시 환경별 절대 경로는 HANDOFF와 비공개 실행 기록을 따른다.

| 파일 | 바이트 | SHA-256 |
| --- | ---: | --- |
| ext4 rootfs 파일 이미지 | 1,073,741,824 | `6ad43a8471ee77e98d930d8c46dbbfb2047c4034f3a38052b8fc98e9578d4e5f` |
| `nura-v26.06-samsung-gta4lwifi-n1-rootfs-only.img.gz` | 193,580,662 | `219551a03244f72618fc65cbc7c64fe914d79a842a0db57c67de26026a4eb613` |

같은 디렉터리의 `manifest.json`에 패키지 버전·APK 캐시/색인·키 해시·입력 SHA·검증 결과를 보존했다. 이는 N1 관측용 manifest이며 기존 portctl 이미지 계약 v1의 완성된 bundle이 아니다.

이 이미지는 파티션 테이블 없는 ext4 filesystem 이미지다. boot 이미지나 SD 전체 이미지가 아니며 기기에 기록하지 않았다. 처음 만든 스냅샷은 build 전용 저장소 경로·키 보존을 보완하기 전 자료라 superseded로 남겼다. 최종 manifest에 대체 사유·이전 해시가 있고 위 `-final` 세트만 현재 준비물로 사용한다.

## 검증

- Nura devicepkg 도구로 로컬 기기 APK 빌드 성공. source SHA-512 검사 포함.
- WSL에서 native chroot·ARM64 QEMU user/binfmt·패키지 설치와 systemd 바이너리 실행 성공. 이는 ARM64 실기기 부팅 검증이 아니다.
- 캐시 APK 465개의 SHA-256, 설치 패키지 362개의 이름·버전·아키텍처, repository index snapshot·공개 키·메타데이터 해시를 보존했다.
- APK 개별 서명 검사에서는 408개가 OK, 57개가 독립 서명 키 UNTRUSTED로 나왔다(종료 57). 이를 전체 실패나 전체 서명 성공으로 숨기지 않는다. 저장소 색인의 신뢰 연결을 별도로 검사하기 위해 같은 버전의 rootfs 패키지 362개를 새 검증 디렉터리에 **오프라인·스크립트 비실행·allow-untrusted 없이** 설치했고 종료 0을 확인했다. 이 결과는 저장소 색인/패키지 checksum 연결 검사이며 개별 서명자 신원 확인과 구분한다.
- `e2fsck -f -n` 종료 0, gzip 해제 결과가 원본 1GiB 이미지의 길이·SHA-256과 일치, WSL→Windows 복사 해시 일치.
- debugfs로 이미지 안의 os-release·repositories를 staging과 대조하고 systemd ELF를 추출해 SHA-256 일치를 확인했다.
- 작업 종료 시 pmbootstrap shutdown 완료, 작업 경로의 mount 해제·이번에 등록한 ARM64 binfmt 해제 확인.

## 실행·로그·해결한 문제

모든 빌드 명령의 cwd는 위 WSL 독립 작업 디렉터리다. Windows 문서/증거 명령의 cwd는 저장소 루트다. source checkout은 일반 사용자, mount/chroot·pmbootstrap은 WSL root로 실행했다.

| 실행 | 결과·로그 |
| --- | --- |
| pinned source fetch/checkout, `pmbootstrap --version`·status | 3.12.1·채널/기기/systemd 확인. 소스별 fetch 로그와 status JSON |
| `install --no-image --no-sshd --no-recommends` | 메타데이터 APK·rootfs 패키지 설치 후 mkinitfs 종료 1. kernel release 목록 `[]` |
| `chroot -r -- apk --print-arch`, systemd version | 각각 종료 0, aarch64·261 |
| N1 계정 잠금·sshd disable, shutdown | 종료 0. 기기·호스트 시스템 서비스를 변경한 것이 아닌 생성 rootfs 설정·빌드 mount 종료 |
| rootfs 준비 이미지 export·e2fsck·gzip·복사 | 종료 0, manifest 및 호스트 로그 |
| 저장소 checksum chain·이미지 내부 검사 | 각각 종료 0, 검증 JSON/로그 |

로그·스크립트·정규화한 관측 JSON은 저장소의 `private/nura/n1/`, WSL의 `logs/`와 `work/log.txt`에 있다. 서명 개인 키·원본 계정 정보는 Git 밖에 남긴다. 로그를 읽을 때 WSL root 접근이 필요할 수 있다. `-l`로 요청한 경로와 별개로 실제 상세 로그는 `work/log.txt`에 기록되어 후속 명령에서 실행별 snapshot을 보관했다.

초기 준비에서 Git 소유권 확인, 도구가 인식하는 기존 canonical remote URL, `origin/main` 채널 목록, kpartx 부재, 새 workdir version marker, boot_size 128 거부를 관측했다. 해당 원인을 확인해 프로세스 범위 Git 설정·공식 redirect URL·채널 ref·kpartx 설치·빈 workdir 초기화·기본 512MiB 설정으로 해결했다. 이 boot_size는 도구 설정이며 실제 기기의 boot 파티션 크기를 뜻하지 않는다. 기존 사용자 파일/소스 초기화·sudoers 변경·기기 쓰기는 하지 않았다.

## 다음 작업

아래는 N1 종료 시점의 작업 목록이다. 후속 [N2 기록](nura-n2-dt-2026-10-30.md)에서 DT·기기 APK·공식 LTS·initramfs 연결과 install 검증을 수행했으며 현재 남은 작업은 HANDOFF를 따른다.

1. 공식 LTS 후보와 SM6115/SM-T500 보드 지원의 차이를 조사한다. 완료 조건: 필요한 DT·driver·firmware·SD/USB 항목과 선별 이식 목록.
2. N2 kernel·DT·module·initramfs를 연결한다. 완료 조건: kernel/flavor 계약을 만족하는 정적 boot 세트·최종 config·해시·로그. 현재 metadata-only package를 boot-ready로 표시하지 않는다.
3. 기기 조사·복구 관문을 확인한다. 완료 조건: 정확한 모델/리비전·터치 변형·파티션·백업·정상 복구 증거. 실제 Nura 부팅은 이 관문 후 진행한다.
