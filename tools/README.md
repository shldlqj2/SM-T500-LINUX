# 기기 조사 도구 v1

Python 3.11 이상·표준 라이브러리로 실행한다. 현재 구현한 명령은 doctor --scope collect, collect, report다. 소스 준비·커널 빌드·artifact 검사는 다음 구현 단계다.

basic·extended 수집과 보고서 생성은 가짜 ADB 및 합성 파일로 검증했다. 실기기 수집·root adapter·부팅·하드웨어 동작은 아직 검증하지 않았다. 전체 기준은 [수집기 설계](../docs/design/01-device-collector.md)와 [데이터 계약](../docs/design/03-data-contracts.md)을 따른다.

## 실행

저장소 루트에서 다음 명령을 사용한다. ADB가 PATH에 없으면 실제 실행 파일을 --adb로 지정한다. Windows에서는 adb.exe가 필요하며 .cmd/.bat 래퍼를 실행하지 않는다. 명시한 경로가 잘못되어도 다른 설치본으로 전환하지 않는다.

~~~text
python tools/portctl.py doctor --scope collect
python tools/portctl.py collect --device-alias tablet-a --profile basic
python tools/portctl.py collect --device-alias tablet-a --profile extended
python tools/portctl.py collect --device-alias tablet-a --profile extended --allow-root
python tools/portctl.py report --run <workspace/private/runs/run-id> --view private
python tools/portctl.py report --run <workspace/private/runs/run-id> --view shareable
~~~

doctor는 ADB version만 확인한다. 실제 조사에는 USB 인증이 완료된 device 상태의 SM-T500/gta4lwifi가 필요하다. 여러 기기가 있으면 --serial로 정확한 대상을 지정한다. ADB가 보고한 transport_id도 있으면 후속 명령에 함께 고정한다.

workspace 기본값은 이 저장소 루트다. 다른 위치에 보관하려면 --workspace <directory>를 지정한다. 결과는 private/runs/<run-id>/run.json, raw/, events.jsonl, reports/에 남는다. 기본 private/는 Git 제외 대상이다. Windows 파일 접근권한은 해당 디렉터리의 기존 ACL도 확인해야 하며 POSIX mode 값만으로 비공개를 보장하지 않는다.

allow-root는 extended에서만 받는다. 대상 식별 통과 이후 읽기 권한 부족이 발생할 때 기존 su -c 'id -u'를 한 번 확인한다. UID 0 확인에 성공한 경우 해당 읽기만 한 번 재시도한다. 승인 거부·timeout·없는 인터페이스의 원래 관측도 보존한다.

## 결과 읽기

complete는 요청한 수집 항목의 관측·형식 검사 통과다. partial은 접근 제한·누락·실패 항목이 남은 상태이고 failed는 환경·대상 식별 등 선행 실패다. 사용자 중단은 interrupted로 기록한다. 각 상태는 실제 부팅·드라이버 동작·복구 성공과 별도로 확인한다.

원본 stdout/stderr는 바이트 그대로 보관하고 크기·SHA-256을 기록한다. 바이너리 exec-out은 원격 exit 상태를 알 수 없어 remote_exit_code=null이다. gzip CRC·DT 길이 검사를 추가한다. ADB client stderr와 stdout는 따로 저장하지만 원격 exec-out stderr는 raw stream에 섞일 수 있다.

private 보고서는 목적·명령·관측 요약·원본 참조·의미·한계를 설명한다. shareable은 허용 목록으로 재구성하며 일련번호·MAC·cmdline·계정·호스트 경로·raw stderr를 제외한다. 입력 장치명은 자동 공개하지 않고 manual 근거가 있는 input.reviewed_names만 공유 후보로 사용한다. 공유 후보 문자열도 길이·식별자·경로 검사와 Markdown escape를 거치며, 공개 전 사람의 검토가 필요하다.

보고서를 생성할 때 run.json의 계약과 원본 파일 크기·해시를 다시 검사한다. 원본을 수정하면 무결성 오류로 중단한다. run.json이 없는 실행은 이벤트 개수와 마지막 불완전한 행만 진단하며 정상 결과로 재구성하지 않는다. 보고서는 새 ID로 만들어 기존 파일을 덮어쓰지 않는다.

| 종료 코드 | 의미 |
| --- | --- |
| 0 | 명령 완료. report의 원래 run 상태는 별도로 유지 |
| 1 | 내부 오류 |
| 2 | CLI·JSON 계약 오류 |
| 3 | ADB·대상·프로토콜·식별 등 선행 조건 부족 |
| 4 | partial 수집 결과 |
| 5 | 파일·경로·무결성 오류 |
| 130 | 사용자 중단 |

일반 읽기는 15초, root 확인·root 읽기·바이너리는 30초 제한이다. 원본은 probe 전체 시도 합계 8MiB, 실행 합계 64MiB로 제한한다. timeout·중단에서는 현재 로컬 ADB client를 종료하며 원격 종료 미확인 한계를 남긴다. collect.lock이 있으면 자동 삭제하지 않고 소유자·프로세스 상태부터 확인한다.

## 합성 검증

~~~text
python -m unittest discover -s tests -v
~~~

tests/fixtures/fake_adb.py는 USB를 사용하지 않는 합성 응답기다. Windows에서는 POSIX shell·SIGINT 항목을 skip하며 Linux/WSL에서 실행한다. tests/test_remote_scripts.py는 고정 경로를 임시 합성 트리로 바꿔 실행하므로 실제 /proc·/sys·block 장치를 읽지 않는다.

검증 중 생성한 합성 원본·로그·보고서는 테스트용 임시 디렉터리에 저장하고 시험 종료 후 정리한다. 따라서 실기기 증거나 개인 백업은 이 검증에서 생성되지 않는다.

## 참고

- [ADB 명령 옵션](https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/docs/user/adb.1.md)
- [ADB exec-out 구현](https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/client/commandline.cpp)
- [Python subprocess](https://docs.python.org/3/library/subprocess.html)
