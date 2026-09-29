# 구현 설계 02. 소스·빌드·산출물 관리

상태: 설계 확정, 코드·기기별 빌드 recipe 미구현, 실제 빌드 미실행.

[개발 환경 계획](../04-development-environment.md)을 CLI와 파일 계약으로 구체화한다. 조사 결과는 [수집기 설계](01-device-collector.md), JSON 필드는 [데이터 계약](03-data-contracts.md)을 따른다.

## 1. 범위와 실행 경계

v1은 고정한 소스·도구 체인을 준비하고 커널·DT 관련 대상·필요 모듈을 빌드해 검사 가능한 묶음을 만든다. rootfs 생성·boot 이미지 조립·기기 기록은 별도 구현이다.

source/build 명령은 Linux에서만 실행한다. Windows에서는 명확한 안내와 코드 3으로 종료하고 WSL을 몰래 시작하지 않는다. doctor/report/artifacts verify는 Windows와 Linux에서 동작한다.

빌드 workspace는 Linux 파일시스템에 지정한다. WSL에서는 /mnt/c 같은 Windows filesystem을 감지하면 build 실행을 중단하고 Linux 경로를 요구한다. ADB 조사 workspace와 build workspace가 달라도 manifest·해시로 연결한다.

소스와 build recipe는 실행 가능한 코드에 준하는 신뢰 대상이다. 해시는 전송·변경 확인 수단이며 다운로드한 코드의 안전성을 보장하지 않는다. 채택 전 build script와 외부 다운로드 동작을 검토한다.

## 2. CLI

~~~text
python tools/portctl.py doctor --scope build
python tools/portctl.py sources sync --lock <sources.lock.json> --workspace <linux-directory>
python tools/portctl.py build plan --recipe <recipe.json> --lock <sources.lock.json> --workspace <linux-directory>
python tools/portctl.py build run --recipe <recipe.json> --lock <sources.lock.json> --workspace <linux-directory> --jobs <positive-int>
python tools/portctl.py artifacts verify --bundle <bundle-directory>
~~~

- build 작업의 --workspace는 필수다. 원래 문서 checkout 위치와 출력 workspace를 구분한다.
- source/recipe 파일 상대 경로는 호출 cwd에서 해석한다. 그 파일 내부 patch/config 경로는 각각 해당 문서가 위치한 디렉터리 기준이다.
- --jobs는 run에서 필수이며 양의 정수다. plan은 실제 병렬 수를 정하지 않고 사용자가 넣어야 할 값을 표시한다.
- plan은 read-only다. 네트워크 다운로드·make·config 생성·package 설치를 하지 않는다.
- run은 plan의 유효성 검사를 다시 수행한다. 이전 plan 성공만 신뢰하지 않는다.
- sources sync만 명시된 소스와 도구 체인의 네트워크 준비를 수행한다. build 실행 중 누락 파일을 자동 다운로드하지 않는다.
- CLI 출력은 한국어 설명이며 기계 판정은 exit code와 JSON 상태를 사용한다.

## 3. 고정 입력과 기기별 데이터

두 입력 문서를 사용한다.

| 문서 | 역할 |
| --- | --- |
| sources.lock.json | 저장소 commit, patch 순서·해시, toolchain·config 파일 해시, 선택 근거 |
| recipe.json | config 구성, 실행 순서, 필요한 host tools, 빌드 대상·산출물 선언 |

lock.state는 draft 또는 ready다. draft에는 미확정 commit/toolchain을 null로 남길 수 있지만 sync/run은 ready만 받는다. plan은 draft를 읽어 누락 사항을 출력하고 코드 3으로 종료한다.

ready에는 실제 기기 조사 ID, 대응 ROM/커널 소스 선택 근거, 모든 입력 해시가 필요하다. 이 조건은 소스 대응 근거의 존재를 요구하며 실제 하드웨어 호환성을 자동 인증하지 않는다.

현재는 기기의 ROM·kernel·vendor와 정상 이미지가 없으므로 실사용 ready lock이나 SM-T500 recipe를 작성하지 않는다. 예시 데이터는 fixture/설명용임을 명시한다.

## 4. 소스 준비 상태 전이

~~~text
lock 검사 → workspace 잠금 → 입력 파일 해시 확인
 → 고정 commit 확보 → submodule/patch 적용 → toolchain 준비
 → 모든 입력 검사 → prepared.json 게시
~~~

소스는 sources/<lock-file-sha256>/ 아래에 준비한다. 준비 중에는 별도 .partial 디렉터리를 쓰고 완료 후 같은 부모 안에서 rename한다. 실패 시 .partial과 로그를 보존한다.

같은 lock 디렉터리가 이미 있으면 prepared 기록과 현재 파일·Git 상태를 검사한다. 일치하면 재사용하며, 불일치·예상 밖 파일·사용자 변경이 있으면 중단한다. git reset --hard, git clean, 강제 checkout으로 수리하지 않는다.

각 Git 저장소는 URL과 완전한 commit ID로 고정한다. branch/tag는 설명용 ref_hint일 뿐 빌드 선택 근거로 쓰지 않는다. 필요한 commit을 fetch할 수 없으면 종료하며 다른 최신 commit을 선택하지 않는다. Git 객체 형식도 lock에 기록한다.

하위 저장소는 경로·URL·commit을 모두 명시한다. 자동 recursive submodule update로 잠금에 없는 코드를 받지 않는다. checkout한 .gitmodules/gitlink와 lock을 대조하고 서로 다르면 중단한다. 모든 필요한 Git 소스는 repo ID로 주소화한다.

patch는 lock에 지정된 순서로 hash 확인 → git apply --check → 적용한다. 기준 tree에서 새로 적용해 staged expected tree ID를 prepared에 기록한다. 재사용 전 현재 index tree와 worktree 상태를 대조해 patch 외 변경을 탐지한다. ignored/untracked 파일도 준비 시 inventory와 대조한다.

소스는 prepared 상태 이후 build 중 변경되지 않는 것이 기본이다. build는 별도 출력 디렉터리를 사용한다. 소스에 생성물을 쓰는 vendor script는 pristine source snapshot의 run 전용 사본에서 실행하고 그 사실·전후 변경을 보고한다. 준비된 공유 source를 자동으로 정리하지 않는다.

## 5. 도구 체인 준비

v1 toolchain 배포 형식은 SHA-256을 고정한 tar 또는 zip archive다. 다운로드 URL, archive 해시, 선택적 strip_prefix, 실행 파일 상대 경로와 version 인수를 lock에 넣는다. 여러 toolchain이 필요하면 ID별로 나열한다.

archive를 private 임시 파일로 받고 해시 통과 후 해제한다. 절대 경로·상위 경로 탈출·device node를 거부한다. archive 내부 symlink는 최종 해석이 toolchain 루트 내부일 때만 허용한다. v1은 archive hardlink 항목을 거부한다. 검증된 일반 배포 archive를 선택하고 미지원 형식을 임의 변환하지 않는다.

정상 파일의 mode와 symlink 정보를 보존한다. PATH 우선순위는 recipe에서 지정한 toolchain bin 디렉터리 순서로 고정한다. 실제 compiler 경로·version·archive 해시를 build 기록에 남긴다.

host make/git/dtc/depmod/modinfo 등은 recipe의 host_tools에 실행 파일·version 명령·필수 여부를 선언한다. doctor는 일반 도구를 안내하고 plan/run은 해당 recipe의 도구를 검사한다. 자동 apt 설치나 sudo 승격은 하지 않는다.

host package snapshot과 OS·Python 버전을 build에 기록한다. v1은 완전한 hermetic 또는 bit-for-bit 재현을 보장하지 않는다. 같은 입력의 기능 재현을 먼저 확보하고 host 차이가 영향을 주면 다음 설계에서 빌드 환경 고정을 강화한다.

## 6. 빌드 실행 단계

| 단계 | 실행·판정 |
| --- | --- |
| preflight | OS·workspace·lock·recipe·prepared·host tools·입력 hash·jobs 검증 |
| configure | 기준 defconfig → 선언 순서의 fragments → olddefconfig |
| config_check | 최종 .config 저장, required_config의 y/m/n/문자열 요구와 대조 |
| compile | recipe의 kernel·DT·외부 모듈 단계를 순차 실행 |
| stage_modules | run별 staging 아래 modules_install 및 depmod |
| inspect | kernel release, module metadata, 요구 산출물·크기 확인 |
| publish | manifest·hash 검사, 임시 bundle을 최종 디렉터리로 전환 |

Kconfig 심볼이 없거나 의존성 때문에 값이 달라지면 config_check에서 중단한다. '=m'과 '=y'를 같은 의미로 허용하지 않는다. 해석되지 않은 요청 심볼을 조용히 무시하지 않는다.

원본 config과 최종 .config를 각각 보존한다. 커널 release는 해당 build context의 make kernelrelease 결과를 기준으로 얻으며 임의의 basename에서 추측하지 않는다.

recipe의 단계는 명시적인 argv·cwd·env로 표현한다. host shell 문자열을 평가하지 않는다. shell 문법이 필요한 vendor script는 고정한 소스 안의 검토된 파일을 interpreter 인수로 실행한다. 무제한 shell -c 문자열을 recipe에 넣지 않는다.

허용 placeholder는 {source:<repo-id>}, {input:<file-id>}, {out}, {staging}, {toolchain:<id>}, {jobs}, {kernel_release}다. input은 preflight에서 해시를 검사하고 run 안에 복사한 입력 파일이다. 각 argv 항목 안에서 치환하되 한 항목을 shell 단어로 재분할하지 않는다. 정의되지 않은 placeholder는 plan에서 오류다. kernel_release는 configure 이후에만 사용할 수 있다.

기본 환경은 필요한 OS 경로/임시 디렉터리 변수, 고정 LC_ALL=C, TZ=UTC와 recipe의 명시 env로 만든다. ambient MAKEFLAGS·ARCH·CC·CFLAGS를 그대로 상속하지 않는다. 사용자 home 변수는 task 변수로 덮어쓰지 않는다.

## 7. 프로세스·로그·중단

run별 build/<run-id>/에 step log, 입력 snapshot, config, 출력, staging을 둔다. 모든 step은 순차 실행하고 내부 make -j만 jobs에 맞춰 병렬화한다.

각 step의 argv·cwd·명시 env·시작/종료·exit code와 stdout/stderr 로그를 비공개 기록에 남긴다. 도구·URL에 자격증명을 넣는 입력은 거부한다. 로그는 디스크에 스트리밍하고 전체를 RAM에 적재하지 않는다.

빌드에는 기본 timeout을 두지 않는다. 사용자는 Ctrl+C로 중단할 수 있으며 진행 상태와 현재 step을 볼 수 있어야 한다. 새 process group에서 실행하고 중단 시 SIGINT → 10초 대기 → SIGTERM → 5초 대기 → SIGKILL 순서로 자기 group만 종료한다. 종료 여부를 확인하지 못하면 cleanup_unconfirmed다.

stdout이 없다고 빌드를 자동 실패로 처리하지 않는다. 디스크 부족·명령 실패 시 현재 step에서 종료하고 로그·작업 디렉터리를 남긴다. 실패·중단된 run은 최종 bundle로 게시하지 않는다.

동일 workspace에서 sync/build는 한 writer만 허용한다. 잠금은 host·PID·시각을 포함하며 stale lock은 자동 삭제하지 않는다. sources sync/build run 둘 다 이 잠금을 사용한다.

v1에는 실패 지점 자동 resume나 ccache 정책을 넣지 않는다. 재실행은 새 run/output을 쓰며 입력과 이전 실행 ID를 연결한다. 유효한 prepared source는 재사용할 수 있다.

## 8. 모듈과 산출물

recipe는 기대 kernel image·config·DT 파일·모듈 존재 여부와 범위를 선언한다. DT가 prebuilt인 경우 빌드된 DT로 가장하지 않고 lock에 명시한 별도 입력으로 추적한다. 실제 boot 패키징은 v1 범위 밖이다.

모듈은 staging/lib/modules/<kernel_release>에 설치한다. depmod를 이 staging으로 실행하며 호스트 /lib/modules에 설치하지 않는다. modinfo의 vermagic·depends를 수집하고 커널 release와 비교한다. CONFIG_MODVERSIONS와 Module.symvers 출처도 기록한다. vermagic 일치만으로 완전한 ABI 검증을 주장하지 않는다.

modules_install이 만든 build/source symlink 중 외부 절대 경로를 가리키는 것은 이식 가능한 bundle에서 제외하고 이유를 적는다. 작업 staging 자체를 숨기거나 수정한 것으로 보고하지 않는다. bundle에 남긴 symlink는 목적지 문자열을 manifest에 기록하고 파일 내용처럼 따라가 해시하지 않는다.

최종 구조는 artifacts/<build-id>/ 아래 manifest.json, checksums.sha256, inputs/, payload/, logs/다. .partial 디렉터리에서 모든 파일을 검사한 뒤 같은 filesystem 안에서 rename한다. 기존 build ID가 있으면 덮어쓰지 않는다.

모듈 유무와 관계없이 payload/build-metadata.json에 입력 해시·커널 release·최종 config 해시·제외 항목을 기록한다. input/config/kernel/metadata/log role을 각각 채우며 정확한 필드는 데이터 계약을 따른다. bundle 게시 후에야 최종 build-run.json의 bundle_path를 설정하므로 이 파일 자체를 bundle 안에 복사해 순환 참조를 만들지 않는다.

manifest는 자기 자신의 해시를 포함하지 않는다. checksums.sha256은 manifest와 나머지 payload·입력·로그의 해시를 포함하되 자기 자신은 제외한다. 이는 전송 무결성 검사이며 서명된 출처 증명은 아니다.

## 9. artifacts verify

Windows/Linux에서 bundle만으로 다음을 검사한다.

1. 지원하는 schema_version·bundle_kind, 정상 완료 상태.
2. required files·필수 role·module policy.
3. 경로 정규화: 절대 경로·'..'·drive prefix·동일 경로 중복 거부.
4. regular file 크기·SHA-256, symlink target과 루트 내부 해석.
5. manifest·checksums 상호 일치와 manifest에 없는 예상 밖 파일 탐지.
6. lock·recipe hash와 input snapshot의 대응.

Windows에서 symlink가 텍스트 파일로 복사되었다면 원래 bundle과 동일하다고 통과시키지 않는다. 오류 보고는 bundle 밖의 private/runs에 저장하며 검사 대상에 새 파일을 만들지 않는다.

통과는 파일 무결성·구성 확인이다. 실기기 boot, 모듈 load, firmware 동작, 복구 가능성은 여기서 판정하지 않는다.

## 10. 구현 검증 시나리오

- draft·누락 commit·잘못된 SHA·미지정 toolchain·미지원 schema 차단.
- 가짜 Git 저장소에서 지정 commit·patch 순서·submodule 불일치 탐지.
- 사용자 변경·예상 밖 untracked 파일 보존, 재사용 source 오염 탐지.
- archive 경로 탈출·외부 symlink·hardlink·hash 오류 차단.
- plan이 다운로드·make·파일 변경을 실행하지 않음.
- config 요구 불일치 때 compile이 실행되지 않음.
- synthetic build script로 성공·실패·신호·자식 프로세스 정리·로그 보존.
- 실패한 run에 완료 bundle이 없고 재실행은 새 디렉터리 사용.
- 전송한 bundle의 변경·누락·크기·symlink·extra file 검사.
- 실제 커널 빌드는 위 검사가 끝난 뒤 대응 소스와 도구 체인이 확보된 시점에 수행.

## 참고

- [Kbuild](https://docs.kernel.org/kbuild/kbuild.html)
- [기존 커널 포팅 계획](../06-kernel-porting.md)
- [부팅 이미지 계약](../05-boot-and-image-design.md)
- [검증 마일스톤](../11-validation-and-milestones.md)
