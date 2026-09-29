# SM-T500 Native Linux

Samsung Galaxy Tab A7 Wi-Fi **SM-T500 / gta4lwifi**에 Debian을 직접 부팅하고, 포팅 과정에서 Linux 커널을 학습하는 프로젝트다.

목표는 터치 가능한 Xfce 데스크톱과 systemd·SSH·Docker를 함께 사용하는 것이다. 화면·터치·Wi-Fi·Bluetooth를 우선 구현하고 나머지 탑재 기능도 장기 지원 대상으로 관리한다.

## 현재 상태

- **구현 설계 단계**: 포팅·복구·검증·학습 계획과 조사 도구·빌드 관리·데이터 계약 설계서를 작성했다. 도구 코드는 아직 없다.
- 사용자 설명: 부트로더 해제·루팅된 LineageOS 설치 상태이며 microSD를 보유하고 있다.
- PC 조사: Windows PowerShell 환경과 WSL2 Ubuntu 24.04 설치를 확인했다.
- 실기기 조사·백업·커널 빌드·이미지 기록·One UI 복구 시험은 **아직 수행하지 않았다**.
- 실기기의 정확한 ROM·커널·vendor 버전 및 파티션·부품 구성은 미확인이다.

계획에 적힌 기대 동작은 이 기기에서 검증된 결과가 아니다. 최신 진행 상황은 [HANDOFF.md](HANDOFF.md)를 기준으로 확인한다.

## 시작하기

1. [에이전트 작업 지침](AGENTS.md)을 읽는다.
2. [최신 인수인계](HANDOFF.md)에서 현재 상태와 다음 작업을 확인한다.
3. [목표와 구조](docs/01-goals-and-architecture.md)를 읽는다.
4. 도구 구현은 아래 구현 설계서를 읽고, 실기기 단계는 [기기 조사](docs/02-device-investigation.md)와 [복구 계획](docs/03-backup-and-recovery.md)을 따른다.

현재 요청 범위는 설계서 작성까지다. 다음 구현 단계는 조사 도구와 합성 fixture 검증이며, 실제 기기 조사는 이후 착수 범위에 맞춰 basic 수집부터 진행한다.

## 구현 설계서

사용자는 '단계별 실행 + 설명 보고서' 방식을 선택했다. 먼저 조사·빌드 관리를 구현 가능한 수준으로 정하고 initramfs 내부 구현은 다음 설계 묶음에서 다룬다.

| 문서 | 확정한 인터페이스 |
| --- | --- |
| [조사 도구](docs/design/01-device-collector.md) | CLI, 대상 선택, probe, root·시간·출력 제한, 부분 실패, 보고서 |
| [빌드·산출물 관리](docs/design/02-build-artifacts.md) | 소스 고정, recipe, 실행 단계, 모듈 staging, 산출물 게시·검사 |
| [데이터 계약 v1](docs/design/03-data-contracts.md) | JSON 필드·상태·종료 코드·근거·개인정보·경로·해시 |

설계서의 명령과 JSON은 향후 구현할 계약이다. 실제 도구·기기별 ready lock·빌드 이미지는 아직 생성하지 않았다.

## 계획 문서

| 문서 | 역할 |
| --- | --- |
| [01 목표·아키텍처](docs/01-goals-and-architecture.md) | 성공 기준, Debian·systemd·Docker·HAL의 관계 |
| [02 기기 조사](docs/02-device-investigation.md) | 모델·파티션·부품·커널·펌웨어 조사 |
| [03 백업·복구](docs/03-backup-and-recovery.md) | 정상 이미지 복귀와 One UI 재설치 |
| [04 개발 환경](docs/04-development-environment.md) | WSL2, 도구 체인, 소스 고정, QEMU |
| [05 부팅·이미지](docs/05-boot-and-image-design.md) | boot, DT, AVB, initramfs, microSD |
| [06 커널 포팅](docs/06-kernel-porting.md) | 기존 커널 재현, 설정, 모듈, 디버깅 |
| [07 하드웨어](docs/07-hardware-enablement.md) | 전체 기능 의존성과 구현 순서 |
| [08 Android HAL](docs/08-android-hal-compatibility.md) | 제한적 호환 계층과 메모리 관리 경계 |
| [09 Debian·GUI·Docker](docs/09-debian-desktop-and-containers.md) | 사용자 공간과 서비스 구성 |
| [10 메모리·전원](docs/10-memory-power-and-stability.md) | 자원 측정, OOM, 충전, 절전 |
| [11 검증·마일스톤](docs/11-validation-and-milestones.md) | E0~E6, 통과 조건, 시험 양식, 일정 |
| [12 커널 학습](docs/12-kernel-learning.md) | 이론·소스 읽기·실험·학습 기록 |
| [13 메인라인](docs/13-mainline-roadmap.md) | upstream 보드 지원과 Debian 13 전환 |
| [설계 결정](docs/decisions.md) | 선택 이유와 재검토 조건 |
| [인수인계 지침](docs/handoff/GUIDE.md) | 세션 종료·에이전트 이전 절차 |
| [인수인계 템플릿](docs/handoff/TEMPLATE.md) | 다음 작업자가 사용할 상태 양식 |

## 기본 방향

기존 부트로더 → 검증된 제조사 계열 커널 → 자체 initramfs → microSD Debian rootfs → systemd 순서로 부팅한다. 초기 Debian 12에서 동작을 확보한 뒤 메인라인과 Debian 13으로 확장한다.

제조사 커널을 사용해도 Debian이 직접 호스트로 실행되면 네이티브 Linux다. 필요할 때 Android HAL을 제한적으로 이용할 수 있지만, 호스트 PID 1은 Debian systemd로 유지한다.

## 문서와 실험 자료

이 저장소에는 계획·설정·패치·재현 절차를 보관한다. 펌웨어·부트 이미지·개인 백업·EFS·보정 데이터 등은 기본적으로 Git 밖에 둔다. 무시 목록은 유출 방지를 보조할 뿐, 공개 전 파일 내용 검사를 대신하지 않는다.

실험은 [검증 양식](docs/11-validation-and-milestones.md)에 따라 기록하며, 미확인 사항은 추측으로 채우지 않는다. 명시적 요청 없이 커밋·푸시·외부 게시·새 에이전트 실행을 수행하지 않는다.
