# SM-T500 Native Linux

Samsung Galaxy Tab A7 Wi-Fi **SM-T500 / gta4lwifi**에 **Nura 26.06**을 직접 부팅하고, 포팅 과정에서 Linux 커널을 학습하는 프로젝트다.

목표는 터치 가능한 Xfce 데스크톱과 systemd·SSH·Docker를 함께 사용하는 것이다. 화면·터치·Wi-Fi·Bluetooth를 우선 구현하고 나머지 탑재 기능도 장기 지원 대상으로 관리한다.

## 현재 상태

- **N2 오프라인 준비 부분 완료**: SM-T500 Wi-Fi 전용 SD·USB 시험 DT를 빌드하고 공식 LTS 6.18.35-r0·모듈·표준 initramfs를 연결했다. `pmbootstrap install --no-image`와 383개 패키지의 저장소 신뢰 경로 검사가 통과했다. [N2 실행 기록](docs/research/nura-n2-dt-2026-10-30.md)에 출처·해시·지원 공백을 보존했다. kernel 자체는 공식 APK이며 로컬 전체 컴파일·boot.img 생성·실기기 부팅은 미실행이다.
- **N1 사용자 공간 준비·검증 완료**: [N1 기록](docs/research/nura-n1-rootfs-2026-10-30.md)의 1GiB ext4 파일은 별도 준비물이다. N1 당시의 mkinitfs 실패는 N2에서 해소했으나 N1 이미지에는 N2 모듈이 없어 N2 대응 rootfs로 사용할 수 없다. [포팅 계획](docs/14-nura-26.06-port-plan.md)·D014·D015를 따른다.
- 조사 CLI·basic/extended probe·비공개/공유 보고서·JSON 계약 검사와 합성 테스트는 구현했다. 이미지·패키지 생성에는 pmbootstrap/Nura 표준 도구를 우선하며 기존 미구현 자체 빌드 엔진은 연동 범위를 다시 정한다.
- 사용자 설명: 부트로더 해제·루팅된 LineageOS 설치 상태이며 microSD를 보유하고 있다.
- 순정 One UI는 하드웨어 관측·firmware 출처·복구 기준으로 사용한다. [제공 T500XXS8CXG1 패키지](docs/firmware/T500XXS8CXG1.md)의 파일 무결성·boot·커널 설정·일부 DT를 정적으로 조사했다. LineageOS 자료 확보는 필수가 아니며 실제 One UI 전환은 아직 수행하지 않았다.
- PC 조사: Windows PowerShell 환경과 WSL2 Ubuntu 24.04 설치를 확인했다.
- 실기기 조사·백업·커널 전체 소스 빌드·기기 이미지 기록·One UI 복구 시험은 **아직 수행하지 않았다**. DT의 전체 binding 검사에는 upstream 비교군과 동일한 GPU 진단이 남아 있다.
- 실기기의 정확한 ROM·커널·vendor 버전 및 파티션·부품 구성은 미확인이다.

계획에 적힌 기대 동작은 이 기기에서 검증된 결과가 아니다. 최신 진행 상황은 [HANDOFF.md](HANDOFF.md)를 기준으로 확인한다.

## 시작하기

1. [에이전트 작업 지침](AGENTS.md)을 읽는다.
2. [최신 인수인계](HANDOFF.md)에서 현재 상태와 다음 작업을 확인한다.
3. [목표와 구조](docs/01-goals-and-architecture.md)를 읽는다.
4. 도구 구현은 아래 구현 설계서를 읽고, 실기기 단계는 [기기 조사](docs/02-device-investigation.md)와 [복구 계획](docs/03-backup-and-recovery.md)을 따른다.

수집기의 실행 방법은 [도구 안내](tools/README.md)에 있다. 다음 작업은 DT 선택·메모리/boot 계약과 대응 SD rootfs·initramfs 실패 정책을 확정하는 것이다. 실기기 basic 수집에는 실제 ADB 설치·연결·인증이 필요하다.

## 구현 설계서

사용자는 '단계별 실행 + 설명 보고서' 방식을 선택했다. 먼저 조사·빌드 관리를 구현 가능한 수준으로 정하고 initramfs 내부 구현은 다음 설계 묶음에서 다룬다.

| 문서 | 확정한 인터페이스 |
| --- | --- |
| [조사 도구](docs/design/01-device-collector.md) | CLI, 대상 선택, probe, root·시간·출력 제한, 부분 실패, 보고서 |
| [빌드·산출물 관리](docs/design/02-build-artifacts.md) | 소스 고정, recipe, 실행 단계, 모듈 staging, 산출물 게시·검사 |
| [데이터 계약 v1](docs/design/03-data-contracts.md) | JSON 필드·상태·종료 코드·근거·개인정보·경로·해시 |

수집기 doctor/collect/report와 collection JSON v1은 구현했다. portctl의 sources/build/artifacts 명령과 ready lock은 미구현이다. 별도 pmbootstrap 경로로 만든 N1/N2 자료는 해당 CLI의 ready bundle이 아니다. 합성 시험 통과는 실기기 지원 증거가 아니다.

D014에 따라 기존 자체 빌드·initramfs 구현 계획은 pmbootstrap/Nura 표준 경로로 대체했다. 위 설계 문서의 공통 출처·해시·상태 계약은 유지하며 실제 연동에 필요한 변경은 후속 설계한다.

## 계획 문서

| 문서 | 역할 |
| --- | --- |
| [01 목표·아키텍처](docs/01-goals-and-architecture.md) | 성공 기준, Nura·systemd·Docker·HAL의 관계 |
| [02 기기 조사](docs/02-device-investigation.md) | 모델·파티션·부품·커널·펌웨어 조사 |
| [03 백업·복구](docs/03-backup-and-recovery.md) | 정상 이미지 복귀와 One UI 재설치 |
| [04 개발 환경](docs/04-development-environment.md) | WSL2, 도구 체인, 소스 고정, QEMU |
| [05 부팅·이미지](docs/05-boot-and-image-design.md) | boot, DT, AVB, initramfs, microSD |
| [06 커널 포팅](docs/06-kernel-porting.md) | 기존 커널 재현, 설정, 모듈, 디버깅 |
| [07 하드웨어](docs/07-hardware-enablement.md) | 전체 기능 의존성과 구현 순서 |
| [08 Android HAL](docs/08-android-hal-compatibility.md) | 제한적 호환 계층과 메모리 관리 경계 |
| [09 Nura·GUI·Docker](docs/09-debian-desktop-and-containers.md) | 사용자 공간과 서비스 구성 |
| [10 메모리·전원](docs/10-memory-power-and-stability.md) | 자원 측정, OOM, 충전, 절전 |
| [11 검증·마일스톤](docs/11-validation-and-milestones.md) | E0~E6, 통과 조건, 시험 양식, 일정 |
| [12 커널 학습](docs/12-kernel-learning.md) | 이론·소스 읽기·실험·학습 기록 |
| [13 메인라인](docs/13-mainline-roadmap.md) | upstream 보드 지원과 장기 유지 |
| [14 Nura 26.06 포팅](docs/14-nura-26.06-port-plan.md) | 공식 기반·입력 고정·기존 포트에서 가져올 범위·단계 |
| [설계 결정](docs/decisions.md) | 선택 이유와 재검토 조건 |
| [인수인계 지침](docs/handoff/GUIDE.md) | 세션 종료·에이전트 이전 절차 |
| [인수인계 템플릿](docs/handoff/TEMPLATE.md) | 다음 작업자가 사용할 상태 양식 |

## 기본 방향

공식 Nura 26.06 aarch64 사용자 공간을 기준으로 SM-T500 전용 kernel·DT·modules/firmware를 연결한다. 기존 Samsung 부트로더 → 호환되는 mainline/LTS kernel과 Nura 표준 initramfs → microSD ext4 rootfs → systemd 순서가 목표다. 이 부팅 경로는 아직 실기기 검증 전이다.

기존 Tab A7 포트의 기기 정보·DTS·필요 드라이버/firmware 변경은 출처와 실제 기기를 대조해 가져온다. 순정 One UI 자료는 하드웨어 조사·복구 기준으로 보존한다. 호스트 PID 1은 Nura의 systemd이며 Docker도 호스트에서 실행한다.

## 문서와 실험 자료

이 저장소에는 계획·설정·패치·재현 절차를 보관한다. 펌웨어·부트 이미지·개인 백업·EFS·보정 데이터 등은 기본적으로 Git 밖에 둔다. 무시 목록은 유출 방지를 보조할 뿐, 공개 전 파일 내용 검사를 대신하지 않는다.

실험은 [검증 양식](docs/11-validation-and-milestones.md)에 따라 기록하며, 미확인 사항은 추측으로 채우지 않는다. 명시적 요청 없이 커밋·푸시·외부 게시·새 에이전트 실행을 수행하지 않는다.
