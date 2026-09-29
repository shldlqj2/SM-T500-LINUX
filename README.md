# SM-T500 Native Linux

Samsung Galaxy Tab A7 Wi-Fi **SM-T500 / gta4lwifi**에 Debian을 직접 부팅하고, 포팅 과정에서 Linux 커널을 학습하는 프로젝트다.

목표는 터치 가능한 Xfce 데스크톱과 systemd·SSH·Docker를 함께 사용하는 것이다. 화면·터치·Wi-Fi·Bluetooth를 우선 구현하고 나머지 탑재 기능도 장기 지원 대상으로 관리한다.

## 현재 상태

- **문서화 단계**: 포팅·복구·검증·학습 계획을 작성했다.
- 사용자 설명: 부트로더 해제·루팅된 LineageOS 설치 상태이며 microSD를 보유하고 있다.
- PC 조사: Windows PowerShell 환경과 WSL2 Ubuntu 24.04 설치를 확인했다.
- 실기기 조사·백업·커널 빌드·이미지 기록·One UI 복구 시험은 **아직 수행하지 않았다**.
- 실기기의 정확한 ROM·커널·vendor 버전 및 파티션·부품 구성은 미확인이다.

계획에 적힌 기대 동작은 이 기기에서 검증된 결과가 아니다. 최신 진행 상황은 [HANDOFF.md](HANDOFF.md)를 기준으로 확인한다.

## 시작하기

1. [에이전트 작업 지침](AGENTS.md)을 읽는다.
2. [최신 인수인계](HANDOFF.md)에서 현재 상태와 다음 작업을 확인한다.
3. [목표와 구조](docs/01-goals-and-architecture.md)를 읽는다.
4. [기기 조사](docs/02-device-investigation.md)와 [복구 계획](docs/03-backup-and-recovery.md)을 진행한다.

지금 해야 할 일은 ADB 연결 환경을 준비하고 읽기 전용 조사를 수행하는 것이다. 이 저장소의 문서를 작성했다는 이유로 기기 변경을 바로 시작하지 않는다.

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
