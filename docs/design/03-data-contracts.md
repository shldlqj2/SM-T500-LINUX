# 구현 설계 03. 데이터 계약 v1

상태: collection v1 reader/writer·계약 validator·합성 테스트 구현. source lock·recipe·build·artifact reader/writer는 후속 구현이다. 아래 JSON 예시는 합성 자료이며 실제 기기 관측·빌드 결과가 아니다.

이 문서는 [수집기](01-device-collector.md)와 [빌드 관리](02-build-artifacts.md)가 공유하는 형식의 기준이다. boot/rootfs/flash 실행 계약은 후속 설계이며 여기서는 kernel bundle까지 정의한다.

## 1. 공통 규칙

- JSON은 UTF-8 without BOM, 들여쓰기 2칸, 파일 마지막 newline, schema_version=1이다.
- 필드명은 snake_case. 필수 필드를 생략하지 않는다. unknown과 not-applicable은 null과 별도 reason으로 구분한다.
- 모든 timestamp는 UTC RFC 3339 문자열이다. Markdown에는 KST를 함께 표시할 수 있다.
- run_id/build_id는 YYYYMMDDTHHMMSSZ-8자리 소문자 hex다. build_id는 성공한 build run의 run_id와 같다.
- SHA-256은 실제 파일 바이트의 64자리 소문자 hex. 정규화한 JSON을 재직렬화해 원본 해시를 계산하지 않는다.
- 상대 파일 경로는 '/' 구분자를 사용한다. 절대 경로·drive prefix·'..'·NUL·루트 밖으로 해석되는 symlink는 이식 가능한 bundle에서 거부한다.
- 문서별 object_kind와 schema_version을 함께 확인한다. 지원하지 않는 version은 추측해서 읽지 않는다.
- v1의 알 수 없는 최상위 필드는 오류로 처리한다. 후속 확장이 필요하면 문서와 reader를 함께 변경한다.
- 원본 증거는 변경하지 않는다. parser 수정 후 해석을 바꾸면 새 report/derived record와 parser_version을 남긴다.

단순 자료형은 Python 표준 라이브러리로 명시적 검사를 구현한다. int 자리에 bool을 허용하지 않고 timestamp·해시·enum·경로를 별도로 검증한다. 외부 JSON Schema 패키지는 v1 필수 의존성에 넣지 않는다.

## 2. 실행 디렉터리

~~~text
private/runs/<run-id>/
  events.jsonl
  raw/<probe-id>/<attempt-index>.stdout
  raw/<probe-id>/<attempt-index>.stderr
  run.json
  reports/<report-id>.private.md
  reports/<report-id>.shareable.md
build/<run-id>/
  inputs/ logs/ out/ staging/
  build-run.json
artifacts/<build-id>/
  manifest.json
  checksums.sha256
  inputs/ payload/ logs/
~~~

raw 확장자는 text/binary를 추정하는 근거가 아니다. 파일 형식은 capture의 content_type에 기록한다. stdout/stderr는 빈 출력도 크기 0인 파일로 생성하며 해시는 해당 빈 파일 값이다. 실행 전 skipped인 경우 파일 참조를 null로 둔다.

events.jsonl은 seq, at, event, item_id, state, error_code를 갖는 구조화 이벤트다. seq는 1부터 증가하며 마지막 불완전한 행은 reader가 무시하고 limitation에 기록한다. 비밀값이나 raw stderr를 event에 복사하지 않는다.

최종 run.json/build-run.json은 같은 디렉터리의 임시 파일을 replace해 게시한다. run 디렉터리 자체는 새 ID로 생성한다. final JSON이 없는 실행은 '미종결'이며 이전 complete로 간주하지 않는다.

## 3. 상태와 종료 코드

### 수집 항목

| status | 의미 |
| --- | --- |
| ok | 명령과 해당 형식 검사를 통과해 관측 가능 |
| unavailable | 필요한 경로·속성·도구 인터페이스가 없음 |
| permission_denied | 읽기 권한 부족 또는 root 승인 거부 |
| timeout | 정해진 시간 안에 완료되지 않음 |
| truncated | 출력 한도 또는 전송 중단으로 완전한 자료 없음 |
| parse_error | 원본은 확보했지만 선언한 형식으로 해석 불가 |
| failed | 위 범주에 해당하지 않는 명령/프로토콜 실패 |
| skipped | 정책·선행 실패·한도·중단으로 실행하지 않음 |

명령 exit 0과 ok는 동의어가 아니다. 빈 필수 속성은 unavailable, 빈 모듈 목록은 ok일 수 있다. 텍스트 오류 메시지만으로 하드웨어 부재를 확정하지 않는다. root 재시도 성공 시 최종 probe는 ok여도 첫 permission_denied attempt는 남긴다.

### 실행 전체

| status | 결정 규칙 |
| --- | --- |
| complete | 요청한 모든 관측이 ok이며 필수 식별 통과 |
| partial | 식별 통과 후 하나 이상 미완료/접근 불가/실패 항목 존재 |
| failed | 필수 환경·대상 식별 실패 또는 build 단계 실패 |
| interrupted | 사용자가 중단했고 그 상태를 기록할 수 있었음 |

명시적 비-root 실행에서 권한 항목이 unavailable이어도 partial로 표시한다. 정상적으로 관측한 '해당 없음'은 ok인 사실 값과 이유로 기록한다. 불명확한 부재는 ok로 바꾸지 않는다.

| exit | 의미 |
| --- | --- |
| 0 | 요청한 명령 완료. report이면 원래 run 상태는 보고서에 별도 표시 |
| 1 | 프로그램 내부 오류 |
| 2 | CLI·입력 문서 형식 오류 |
| 3 | 도구·대상·draft·필수 입력 등 선행 조건 부족 |
| 4 | partial 수집 결과 생성 |
| 5 | 명령 수행 또는 무결성 검증 실패 |
| 130 | 사용자 중단 |

error_code는 null 또는 아래 고정 값이다. 새 코드가 필요하면 코드와 계약을 함께 추가한다.

~~~text
tool_missing, tool_failed, unsupported_platform, invalid_arguments,
invalid_schema, no_device, multiple_devices, unauthorized, offline,
unsupported_device_state, model_mismatch, identity_unverified,
protocol_unsupported, device_disconnected, path_unavailable,
permission_denied, root_unavailable, timeout, output_limit, output_budget,
parse_error, command_failed, user_interrupted, cleanup_unconfirmed,
incomplete_run, draft_input, lock_busy, input_mismatch, source_dirty,
unsafe_path, unsupported_archive, download_failed, config_mismatch,
artifact_missing, artifact_mismatch, unexpected_artifact, internal_error
~~~

error_code와 status는 다른 축이다. 예를 들어 partial/device_disconnected와 failed/model_mismatch를 구분한다. raw 로그를 공유 오류 문자열로 재사용하지 않는다.

## 4. run.json

| 필드 | 형식·의미 |
| --- | --- |
| object_kind | 문자열 device_collection |
| schema_version, run_id | 공통 규칙 |
| started_at, finished_at | UTC 시각 |
| tool_revision | git_commit: string/null, dirty: bool, source_files: FileDigest 배열 |
| host | os, python_version, adb_path, adb_version: 문자열, cwd: 문자열 |
| device_alias | 사용자 지정 비민감 별칭 |
| target | serial: string/null, adb_state: string/null. 비공개 전용 |
| profile, allow_root | basic/extended, bool |
| status, error_code | 공통 enum |
| probes | Probe 배열, 정의한 실행 순서 |
| facts | Fact 배열 |
| limitations | code·item_id·note를 갖는 배열 |

FileDigest는 path(string), size_bytes(0 이상의 int), sha256(string) 필드를 갖는다. path는 도구 소스 루트 기준 상대 경로이며 sha256은 공통 해시 규칙을 따른다. tool_revision.source_files는 실제 실행 도구 코드의 FileDigest 배열이다. Git dirty인 개발 도구도 수집은 가능하되 그 실행 코드 목록을 남긴다. 단순 commit ID만으로 로컬 수정이 없는 것처럼 보이지 않게 한다.

Probe 필드는 id, parser_version, required, status, error_code, attempts다. required는 대상 식별·kernel.release 등에 적용하며 프로필의 나머지 누락도 전체 partial 판정에 반영한다.

collector의 진단 probe ID는 host.adb_version, transport.devices, transport.shell_ok, transport.shell_fail, privilege.root다. 마지막 항목은 root 확인이 필요한 경우에만 존재한다. complete/partial 실행은 observed 모델·코드명과 해당 probe의 ok 상태를 모두 요구한다. 현재 parser_version은 1이며 reader가 모르는 버전·probe ID는 거부한다.

Attempt 필드는 privilege(shell/root), argv(string 배열), started_at, duration_ms, host_exit_code(int/null), remote_exit_code(int/null), status, error_code, stdout(Capture/null), stderr(Capture/null)다. argv는 serial 등 비공개 값이 포함될 수 있으므로 private 기록에만 둔다.

Capture는 path, size_bytes, sha256, content_type(text/binary), truncated(bool)다. raw 텍스트 디코딩 실패에도 원본은 유지하고 report에서만 replacement 처리한다. 해석에 영향을 주면 parse_error다.

Fact는 key, value(JSON scalar/array/object/null), unit(string/null), source_probe(string/null), evidence(observed/manual), reason(string/null), annotation(object/null)이다. manual은 annotation에 author, at, basis를 필수로 둔다. 자동 parser는 manual 기록을 만들지 않는다.

아래는 합성 fact 예시다. 실제 실행 결과가 아니며 full run.json을 뜻하지 않는다.

~~~json
{
  "key": "kernel.release",
  "value": "4.19.0-fixture",
  "unit": null,
  "source_probe": "kernel.release",
  "evidence": "observed",
  "reason": null,
  "annotation": null
}
~~~

실패한 관측의 예시는 다음과 같다.

~~~json
{
  "key": "kernel.config",
  "value": null,
  "unit": null,
  "source_probe": "kernel.config",
  "evidence": "observed",
  "reason": "permission_denied",
  "annotation": null
}
~~~

여기서 observed는 'null이라는 실제 하드웨어 값'을 뜻하지 않고 수집 시도에서 얻은 상태를 뜻한다. 소스 commit 후보·추정 부품을 자동 Fact로 추가하지 않는다.

## 5. 공유 보고서 허용 목록

shareable은 object_kind, schema_version, run_id, tool_revision.git_commit, device_alias, profile, status, probe ID·최종 status·고정 error 설명을 사용할 수 있다. host·target·attempt argv·raw 경로·raw 출력·자유형 note는 제외한다.

facts에서는 identity.model, identity.codename, identity.rom_build, identity.vendor_build, identity.bootloader, kernel.release, memory.total_bytes, input의 검토한 장치명, storage의 비식별 파티션 이름·용량만 허용한다. cmdline·mount 목록·MAC·serial·UUID·SSID·계정·사용자 경로는 제외한다.

허용 목록의 문자열도 길이·제어문자·Markdown escape와 식별자 패턴 검사를 통과해야 한다. 넘친 값은 원문 대신 withheld와 이유를 표시한다. 이 검사는 사람의 공개 전 검토를 대체하지 않으며 report는 자동으로 docs에 복사하지 않는다.

## 6. sources.lock.json

| 필드 | 형식·의미 |
| --- | --- |
| object_kind, schema_version | source_lock, 1 |
| lock_id, state | 비민감 식별자, draft/ready |
| target | model, codename, arch(arm64) |
| evidence | collection_run_id, baseline_id, rationale: string/null |
| repositories | Repository 배열 |
| toolchains | Toolchain 배열 |
| files | InputFile 배열 |

Repository: id, url, object_format(sha1/sha256), commit(string/null), ref_hint(string/null), submodules(array), patches(array). commit은 객체 형식에 맞는 완전한 40/64자리 hex다. submodule은 path, repo_id를 가져 repositories의 정확한 항목을 참조한다. patches는 순서가 있는 file_id 배열이다.

InputFile: id, role(patch/config/prebuilt), path, size_bytes(int/null), sha256(string/null). path는 lock 위치 기준이며 비공개 기기 파일은 공개 Git에 포함하지 않는다. source file을 준비하려면 유효한 file entry로 연결한다.

Toolchain: id, archive_url, archive_sha256, archive_format(tar/zip), strip_prefix(string/null), bin_dirs(string 배열), executables(array). executable 항목은 name, path, version_args(string 배열), expected_version(string/null)이다. ready에서는 URL/hash/경로가 확정되어야 하며 실제 version은 prepared/build에 별도 저장한다.

ready는 모든 참조 ID가 유효하고 commit·파일 해시·archive 해시·선택 근거가 있어야 한다. draft의 null을 최신 버전으로 자동 보완하지 않는다. 재귀 submodule 참조의 cycle과 중복 경로를 거부한다.

## 7. recipe.json

필드는 object_kind(build_recipe), schema_version, recipe_id, target, kernel_repo_id, host_tools, env, path_toolchains, configure, steps, expected_outputs, modules다.

- host_tools: name, executable, version_args, required를 갖는 배열. executable은 명시 경로 또는 PATH 이름.
- env: 허용 환경변수의 문자열 map. 빈 값·공백을 shell로 해석하지 않는다.
- path_toolchains: lock의 toolchain ID를 순서대로 나열한다.
- configure: defconfig(string), fragment_ids(순서 있는 file ID 배열), commands(Command 배열), required_config(map).
- configure.commands는 defconfig 생성, fragment 병합, olddefconfig를 실행하는 source별 정확한 argv다. defconfig/fragment_ids는 선택한 입력을 선언하고 commands는 실행 방법을 정의한다. plan은 commands가 선언 입력을 참조하는지 확인한다.
- required_config의 값은 y/m/n 또는 Kconfig 문자열·숫자 표현이다. '# CONFIG_X is not set'과 '=n'은 n으로 정규화하고 다른 값은 임의 동등 처리하지 않는다.
- steps: phase(compile/stage_modules/inspect)를 가진 Command 배열. configure 이전 실행이나 publish 뒤 실행은 없다.
- modules: required(bool), staging_subdir(string), metadata_required(bool). required이면 대응 모듈이 하나 이상 있어야 한다.
- expected_outputs: role, root(source/out/staging/input), root_id(string/null), path, pattern(bool), required(bool)를 가진 배열. wildcard는 고정 디렉터리 안에서 정렬해 확장한다.

Command는 id, argv(string 배열), cwd(string), env(map), timeout_seconds(int/null)다. build 기본 timeout은 null이고 source별 필요가 명시된 경우에만 설정한다. argv는 최소 1개 항목이며 shell 문자열로 join해 실행하지 않는다.

placeholder는 {source:<id>}, {input:<id>}, {toolchain:<id>}, {out}, {staging}, {jobs}, {kernel_release}다. 목록 확장·임의 Python 식·환경변수 표현은 없다. cwd는 검증한 source/run 경로 안이어야 한다.

실제 source별 defconfig·명령·artifact path는 조사 후 채우는 데이터다. 미확정 recipe는 실행하지 않는다. Windows shell이나 실제 기기 명령을 build recipe에 넣지 않는다.

## 8. prepared.json과 build-run.json

prepared.json 필드: object_kind(prepared_sources), schema_version, lock_sha256, prepared_at, repositories, toolchains, input_files, files_inventory_sha256. repositories는 id·base_commit·expected_tree·patch_hashes를 저장한다. toolchains는 id·archive_sha256·실제 version 결과를 기록한다. sources sync 결과 검증에 사용하며 source snapshot과 함께 로컬 보관한다.

build-run.json 필드: object_kind(build_run), schema_version, run_id, started_at, finished_at, status, error_code, tool_revision, host, lock_sha256, recipe_sha256, jobs, steps, kernel_release, config_sha256, bundle_path, limitations.

build host에는 OS·Python·host_tools version·명시 환경·패키지 snapshot 경로를 넣는다. bundle_path는 성공 전 null이다. step 기록은 id, phase, argv, cwd, env, started_at, duration_ms, exit_code, status, stdout_file, stderr_file을 갖는다. build step status는 succeeded/failed/interrupted/skipped다.

실패한 빌드의 kernel_release/config_sha256이 이미 관측됐다면 보존한다. 오류를 숨기기 위해 값을 전부 null로 되돌리지 않는다. manifest 게시 전 crash는 완료 bundle로 보지 않는다.

## 9. manifest.json: kernel bundle

| 필드 | 형식·의미 |
| --- | --- |
| object_kind, schema_version | artifact_manifest, 1 |
| bundle_kind, build_id, status | kernel, run ID, complete |
| created_at, target | 시각, model/codename/arch |
| inputs | lock_sha256, recipe_sha256, tool_revision, sources, toolchains, file_refs |
| kernel | release, config_path, image_path, module_root(string/null), module_metadata_path(string/null) |
| validation | build(succeeded), hardware(not_run), limitations(array) |
| files | BundleFile 배열 |

file_refs는 원래 input ID와 bundle 내 snapshot path를 연결한다. sources는 실제 commit·patch/tree를, toolchains는 실제 archive hash·version을 기록한다. lock의 상대 입력 경로가 다른 PC에 없어도 snapshot 파일로 hash 대응을 검사한다.

BundleFile은 path, kind(file/symlink), role(input/config/kernel/dtb/dtbo/module/metadata/log), size_bytes(int/null), sha256(string/null), target(string/null)이다. file이면 크기·해시 필수, target=null이다. symlink면 target 필수, size/hash=null이다.

files에는 manifest.json과 checksums.sha256 자체를 넣지 않는다. checksums.sha256은 manifest와 모든 regular file을 정렬된 상대 경로로 나열한다. symlink는 manifest의 target으로 검증한다. 외부 경로 링크·broken link·symlink cycle은 실패다. bundle 내부 경로는 대소문자를 보존하며 Windows에서 충돌하는 이름을 거부한다.

필수 role은 input, config, kernel, metadata, log이며 각각 하나 이상의 regular file이 있어야 한다. metadata에는 payload/build-metadata.json을 포함한다. 이 파일은 object_kind(build_metadata), schema_version(1), build_id, lock_sha256, recipe_sha256, kernel_release, config_sha256, excluded_entries를 갖는다. excluded_entries는 bundle에서 제외한 staging 항목의 path·reason 배열이며 없으면 빈 배열이다. build-metadata는 bundle_path나 manifest 해시를 포함하지 않아 순환 참조를 만들지 않는다. DT·module 요구는 recipe의 expected_outputs/modules에 따른다. kernel.module_root가 null이면 module_metadata_path도 null이어야 한다. /lib/modules의 host 절대 경로가 bundle 필드에 들어가면 오류다.

validation.hardware는 생성 시 항상 not_run이다. 이후 실기기 시험은 bundle을 수정하지 않고 별도 experiment record로 build_id를 참조한다. 배포·기기 기록 가능 여부는 이 manifest의 complete에서 추론하지 않는다.

## 10. 검증과 변경 정책

계약 검사에서는 required field, 자료형, enum, 참조 ID, 해시, 경로, 완료 상태와 파일 간 대응을 검증한다. 테스트 fixture는 정상 complete, 권한 부족 partial, 식별 실패 failed, 사용자 중단 interrupted, 미종결 디렉터리, 손상 bundle을 포함한다.

문서 예시는 문법 검사를 하고 실제 기록과 섞지 않는다. 스키마 변경 시 세 설계서·reader/writer·fixture를 함께 갱신한다. 새 필드를 소비자가 무시해도 안전한지 결정하지 않은 채 출력만 늘리지 않는다.
