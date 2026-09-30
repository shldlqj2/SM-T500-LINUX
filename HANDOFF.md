# 최신 인수인계 — 수집기 v1 구현

## 갱신·전달 상태

- 갱신 시각: 2026-09-30T14:45:11+09:00 수집기 구현 커밋·푸시 결과 반영.
- 작성 주체: 현재 주 에이전트.
- 현재 단계: 수집기 v1 구현·합성 검증 완료, 실기기 M0 착수 전.
- 기록 상태: doctor/collect/report·basic/extended probe·collection JSON 계약 검사·설명 보고서 구현. 실기기 수집과 빌드 도구는 미실행·미구현.
- 실제 소유권 이전: 요청 없음. 다른 에이전트 실행·메시지 전송·worktree 생성 없음.

## 목표와 현재 요청 범위

사용자는 SM-T500에 네이티브 Debian/Ubuntu를 포팅하며 커널을 학습하려 한다. 합의한 초기 기준은 Debian 12 minimal, 제조사 계열 커널, microSD ext4, systemd host PID 1, 터치 Xfce, Docker 웹/API 작업이다. 제한적 Android HAL은 허용하며 전체 기능과 One UI 재설치 경로를 유지한다.

사용자가 '이제 설계서에 따라 작업 시작'을 요청했다. D010의 단계별 실행에 따라 첫 구현 단계인 수집기와 합성 검증을 완료했다. 다음 구현 단계는 빌드 관리다. 실기기 수집에는 ADB·연결·인증이 필요하고 현재 환경에서 PATH의 ADB는 확인되지 않았다. initramfs 내부 구현은 후속 설계 묶음이다.

이미 합의한 선택은 [결정 기록](docs/decisions.md)에 있다. 사용자에게 배포판·GUI·학습 경험·복구 범위를 다시 묻지 않는다.

## 저장소·환경

- Windows 경로: C:\Users\SSAFY\orca\projects\PlayGround\SM-T500-LINUX
- Shell: PowerShell.
- Branch: master.
- 수집기 구현 작업 시작 시 HEAD: 61351399946b165e3a261d7c5b472b18cf4d2f37, `docs: record design push in handoff`.
- 설계 문서 commit: 7631e5a, `docs: specify collector and build artifact contracts`.
- 기존 문서: 위 HEAD까지 origin/master 추적 ref와 일치했고 이번 작업 시작 시 worktree는 깨끗했다.
- 수집기 구현 commit: `36c02c7`, `feat: implement SM-T500 device collector`. 수집기·테스트·설계/안내 문서 23개 파일을 포함하며 `origin/master` 푸시를 완료했다.
- WSL2: Ubuntu-24.04 설치를 확인했다. 커널 빌드용 패키지·디스크·메모리 설정은 미검증이다.
- Python: Windows 3.12.10, WSL Ubuntu-24.04 3.12.3에서 합성 시험을 실행했다.
- ADB: 이번 doctor --scope collect 결과 tool_missing·종료 코드 3. 현재 PATH에서 찾지 못한 결과이며 PC 전체에 없다고 확정한 것은 아니다. 실기기 연결·root는 검사하지 않았다.

수집기 구현은 `36c02c7`로 커밋해 `master`에 기록하고 `origin/master`에 푸시했다. 푸시 후 로컬 HEAD와 `origin/master`가 일치하고 worktree가 깨끗한 것을 확인했다. [전달 지침](docs/handoff/GUIDE.md)에 따라 실제 변경 파일을 전달한다.

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
| 설계 문서 commit·push | 완료 | 7631e5a, master → origin/master |
| 수집기 doctor/collect/report | 구현·합성 검증 완료 | tools/portctl.py, tools/portlib/, tools/README.md |
| 기본·확장 probe와 root 관문 | 구현·합성 검증 완료 | 정확한 식별 후 상세 읽기·필요 항목만 root 재시도 |
| collection v1 계약·원본 무결성 | 구현·합성 검증 완료 | strict reader/writer, 상태·참조·해시 검사 |
| Windows·Linux 동작 | 합성 검증 완료 | 아래 테스트 결과. 실제 ADB 및 태블릿 검증과 별개 |
| 실제 기기 수집 | 미실행 | ADB 설치·연결·인증 필요 |
| sources/build/artifacts CLI | 미구현 | docs/design/02·03 설계만 존재 |

## 중요한 발견·미확인 사항

- 공개 LineageOS와 Ubuntu Touch의 ramdisk offset 표기가 다르다. 정상 boot.img 분석 전 어느 값을 채택하지 않는다.
- 공개 LineageOS source에는 cgroups·OverlayFS·seccomp·PSI·pstore 설정이 있으나 실제 최종 config와 런타임 동작은 미확인이다.
- 공개 터치 드라이버 설정으로 실물 터치 부품을 확정하지 않는다.
- 기존 Ubuntu Touch 포트는 Bluetooth를 실험 단계로 표시한다. 우리 Debian의 동작 증거가 아니다.
- 실제 모든 부팅·서비스·하드웨어·복구 시험은 미실행이다.
- 구현 기준은 docs/design/03-data-contracts.md의 JSON·상태·종료 코드다. 기기별 ready lock·recipe의 값은 아직 미확정이다.
- exec-out에는 원격 종료 frame이 없으므로 binary remote_exit_code는 null이며 형식 검사로 읽기를 판정한다. root adapter의 실제 ROM 호환성은 아직 미확인이다.
- 등록된 driver/sysfs 항목은 실제 하드웨어 사용 성공을 증명하지 않는다. 접근 불가·없는 선택 속성은 partial로 남을 수 있다.

## 진행 중 작업·산출물

- 기기 빌드·다운로드·플래싱·백그라운드 실험 프로세스: 없음.
- 커널·부팅 이미지·rootfs·firmware 산출물: 없음.
- 개인 백업·EFS·원본 기기 덤프: 수집하지 않음.
- 정상 복귀 세트: 미확보. docs/03 절차를 먼저 진행해야 함.
- 인수인계 이력: 실제 이전이 없어 history snapshot을 만들지 않음.
- 합성 원본·로그·보고서: 테스트 임시 디렉터리에서 생성 후 정리했다. 실기기 증거를 생성하지 않았다. 테스트 콘솔 결과는 이 세션의 도구 출력이며 별도 상주 원본 로그 파일은 보관하지 않았다.

## 다음 작업: 최대 3개

1. 빌드 관리 도구를 합성 소스·작은 fixture로 구현.
   - docs/design/02·03의 lock·recipe·config 관문·bundle 검사와 중단 처리를 구현한다.
   - 완료 조건: 사용자 소스 보존, 고정 입력, 실패 로그, 산출물 무결성 시험 통과. 기기별 source SHA는 미확정으로 유지.
2. 실제 ADB 설치 경로·USB 연결·인증을 확인하고 basic 수집.
   - tools/README.md와 docs/02를 읽고 --adb 및 필요 시 --serial로 정확한 대상을 지정한다. root는 기본적으로 허용하지 않는다.
   - 완료 조건: 실제 조사 보고서, 수동 읽기와 값·원본 비교, ROM/vendor/kernel·소스 대응 근거와 미확인 목록. 실제 자료는 private/에 보관한다.
3. 정상 이미지·백업·복구 관문 준비.
   - docs/03에 따라 실측 파티션과 대응 firmware·개인 자료를 확인한다.
   - 완료 조건: 해시가 있는 복귀 세트·백업 목록·복구 조건. 기기 기록은 해당 관문과 요청 범위를 확인한 뒤 진행한다.

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
