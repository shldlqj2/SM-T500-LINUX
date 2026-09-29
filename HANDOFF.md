# 최신 인수인계 — 조사·빌드 도구 구현 설계

## 갱신·전달 상태

- 갱신 시각: 2026-09-29T17:05:02+09:00 검증 결과 반영.
- 작성 주체: 현재 주 에이전트.
- 현재 단계: M0 착수 전, 조사·빌드·산출물 도구의 구현 설계 완료.
- 기록 상태: 구현 설계서 3개 작성 및 기존 문서 연결, 문서 정적 검증 완료. 도구 구현·실기기 검증은 미실행.
- 실제 소유권 이전: 요청 없음. 다른 에이전트 실행·메시지 전송·worktree 생성 없음.

## 목표와 현재 요청 범위

사용자는 SM-T500에 네이티브 Debian/Ubuntu를 포팅하며 커널을 학습하려 한다. 합의한 초기 기준은 Debian 12 minimal, 제조사 계열 커널, microSD ext4, systemd host PID 1, 터치 Xfce, Docker 웹/API 작업이다. 제한적 Android HAL은 허용하며 전체 기능과 One UI 재설치 경로를 유지한다.

이번 실행 요청은 합의한 1차 구현 설계를 Markdown에 반영하는 것이다. 사용자는 설계 구체화를 먼저 요청했으며 이번 범위는 도구 코드 구현·실기기 조사·빌드·flash를 포함하지 않는다. 단계별 실행과 설명 보고서 방식을 선택했고 initramfs 내부 구현은 다음 설계 묶음이다.

이미 합의한 선택은 [결정 기록](docs/decisions.md)에 있다. 사용자에게 배포판·GUI·학습 경험·복구 범위를 다시 묻지 않는다.

## 저장소·환경

- Windows 경로: C:\Users\SSAFY\orca\projects\PlayGround\SM-T500-LINUX
- Shell: PowerShell.
- Branch: master.
- HEAD: de4ad089eeb75fa82647a682697dc0cef9565fbf, docs: add SM-T500 Linux porting plan.
- 기존 문서: 위 첫 커밋이 origin/master에 푸시된 상태이며 이번 시작 시 worktree는 깨끗했다. 원격 반영은 앞선 push 성공과 현재 tracking ref 일치에 근거한다.
- 현재 변경: 조사·빌드 설계서 3개와 연결 문서 7개를 `docs: specify collector and build artifact contracts` 커밋으로 반영했다. 이후 origin/master 푸시 상태는 아래 Git 검증 기록을 따른다.
- WSL2: Ubuntu-24.04 설치를 확인했다. 커널 빌드용 패키지·디스크·메모리 설정은 미검증이다.
- ADB: 현재 PATH와 이전에 조사한 일부 후보 디렉터리에서 찾지 못했다. PC 전체에 없다고 확정한 것은 아니다.

기존 문서와 이번 설계 변경은 Git commit으로 전달할 수 있다. 새 checkout에서는 현재 master의 push 반영 여부를 확인한다. [전달 지침](docs/handoff/GUIDE.md)을 따른다.

## 기기 상태

| 항목 | 현재 알려진 상태 | 근거 |
| --- | --- | --- |
| 모델 | SM-T500 | 사용자 설명 |
| OS | LineageOS | 사용자 설명, 정확한 버전 미확인 |
| 부트로더·root | 해제·루팅 상태 | 사용자 설명, 직접 검사 미실행 |
| microSD | 보유 | 사용자 설명, 용량·파일시스템 미확인 |
| 현재 USB 연결·boot 모드 | 미확인 | 이전 PC 조회에서 ADB 태블릿 발견 못함 |
| kernel/vendor/bootloader revision | 미확인 | 실기기 조사 미실행 |
| 마지막 기기 기록 | 없음 | 이번 작업에서 기기 변경 안 함 |
| 백업·복구 시험 | 미실행 | 계획만 있음 |
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
| 설계 문서 commit·push | 진행 중 | commit 생성 완료, origin/master 반영 확인 후 완료로 갱신 |

## 중요한 발견·미확인 사항

- 공개 LineageOS와 Ubuntu Touch의 ramdisk offset 표기가 다르다. 정상 boot.img 분석 전 어느 값을 채택하지 않는다.
- 공개 LineageOS source에는 cgroups·OverlayFS·seccomp·PSI·pstore 설정이 있으나 실제 최종 config와 런타임 동작은 미확인이다.
- 공개 터치 드라이버 설정으로 실물 터치 부품을 확정하지 않는다.
- 기존 Ubuntu Touch 포트는 Bluetooth를 실험 단계로 표시한다. 우리 Debian의 동작 증거가 아니다.
- 실제 모든 부팅·서비스·하드웨어·복구 시험은 미실행이다.
- 구현 기준은 docs/design/03-data-contracts.md의 JSON·상태·종료 코드다. 기기별 ready lock·recipe의 값은 아직 미확정이다.

## 진행 중 작업·산출물

- 기기 빌드·다운로드·플래싱·백그라운드 실험 프로세스: 없음.
- 커널·부팅 이미지·rootfs·firmware 산출물: 없음.
- 개인 백업·EFS·원본 기기 덤프: 수집하지 않음.
- 정상 복귀 세트: 미확보. docs/03 절차를 먼저 진행해야 함.
- 인수인계 이력: 실제 이전이 없어 history snapshot을 만들지 않음.

## 다음 작업: 최대 3개

1. 사용자에게 도구 구현 착수 요청이 오면 수집기 CLI와 계약부터 구현.
   - docs/design/01·03을 기준으로 argv runner, probe, JSON 기록, 설명 보고서를 만든다.
   - 완료 조건: fake ADB로 기기 선택·권한·timeout·부분 실패·바이너리·비공개/공유 보고서 검증. 실제 기기 동작으로 표기하지 않음.
2. 빌드 관리 도구를 합성 소스·작은 fixture로 구현.
   - docs/design/02·03의 lock·recipe·config 관문·bundle 검사와 중단 처리를 구현한다.
   - 완료 조건: 사용자 소스 보존, 고정 입력, 실패 로그, 산출물 무결성 시험 통과. 기기별 source SHA는 미확정으로 유지.
3. 실기기 조사 착수 요청 범위가 확인되면 basic 수집과 기준표 작성.
   - ADB 연결과 정확한 모델부터 확인하고 필요한 extended 관측·소스 대응·백업 준비로 진행한다.
   - 완료 조건: 실제 조사 보고서, 미확인 목록, 대응 소스 근거와 복구 준비 항목. 커스텀 이미지 기록은 docs/03 관문 이후.

## 반복 금지·주의

- 계획 문서의 체크리스트를 실기기 검증 완료로 해석하지 않는다.
- Git HEAD는 이미 존재한다. 아직 없는 도구 코드·기기 이미지·백업 경로를 존재한다고 쓰지 않는다.
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
- Git 검사: git diff --check 통과. LF→CRLF 안내는 있었으나 공백 오류는 없었다. 검증 당시 HEAD와 로컬 origin/master 추적 ref는 de4ad08로 일치했다. 그 뒤 사용자 요청으로 새 설계 커밋을 생성했다. origin/master 푸시 여부는 아래에서 확인 후 기록한다.
- 계약 대조: CLI의 미구현 표기, source lock의 draft/ready 경계, 수집 partial·중단 상태, 개인정보 공유 제한, bundle 필수 role과 FileDigest 필드 정의를 점검했다.
- 수정: 모듈이 없는 bundle도 build-metadata를 갖도록 명시하고 manifest·최종 build-run 사이의 순환 참조를 피하도록 정리했다.
- 한계: JSON 문법 확인은 계약 validator 시험이 아니다. 외부 링크 가용성·렌더링·도구 코드·실제 빌드·실기기 시험은 검증하지 않았다.
