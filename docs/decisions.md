# 설계 결정 기록

이 문서는 이미 합의한 선택과 이유를 보존한다. 현재 사용자 지시나 관측 결과로 변경이 필요하면 이전 결정을 지우지 말고 대체 결정과 연결한다. 날짜는 2026-09-29, 시간대는 Asia/Seoul을 기준으로 초기 작성했다.

## D001. 제조사 커널에서 시작

- 상태: 과거 채택, 2026-10-30 D014로 대체.
- 배경: 사용자는 부팅 실패 위험을 줄이면서 네이티브 Linux와 커널 학습을 원한다.
- 선택: 현재 동작하는 Samsung/LineageOS 계열 커널을 재현한 뒤 Debian용 변경을 추가한다. 메인라인은 별도 장기 단계다.
- 기준 ROM 구체화: 2026-10-30 [D013](#d013-one-ui를-포팅-기준-rom으로-선택)에 따라 순정 One UI로 전환할 계획이다. 제조사 계열 커널에서 시작하는 방향은 유지한다.
- 영향: vendor driver 지원을 활용하되 구형 커널 ABI·보안 유지·사용자 공간 호환성을 별도 관리한다.
- 재검토: 기준 소스 재현 불가, 필수 사용자 공간 기능 구현 불가, upstream 지원이 더 완성된 경우.
- 대체: 2026-10-30 D014에서 Nura 26.06 호환 mainline/LTS 우선으로 변경했다. 제조사 커널·One UI 자료는 하드웨어 조사·복구 기준으로 남긴다.

## D002. Debian minimal과 단계적 배포판 전환

- 상태: 과거 설계 기본값, 2026-10-30 D014로 대체.
- 배경: 사용자는 Ubuntu/Debian 중 경량 구성을 선호한다.
- 선택: Debian 12 arm64 minimal을 초기 4.19 실험 기준으로 두고 메인라인 단계에서 Debian 13으로 확장한다.
- 이유: 패키지·서비스를 좁히고 구형 커널과 초기 변수를 줄인다. 버전 자체가 가벼움의 근거는 아니다.
- 영향: support 기간·개별 패키지·kernel/runtime 요구를 실제 설치 시 확인한다.
- 재검토: Debian 12 지원 조건 악화, 필수 패키지 문제, 더 적합한 검증 조합 발견.
- 대체: 2026-10-30 사용자 선택으로 D014의 Nura 26.06/aarch64가 초기 배포판이 됐다. Debian 12→13 전환은 현재 기본 계획에서 제외한다.

## D003. microSD rootfs와 내부 변경 최소화

- 상태: 채택.
- 선택: 내부 boot 이미지에서 SD ext4의 Debian으로 전환한다. 내부 재파티셔닝·Linux rootfs 설치는 기본 범위 밖이다.
- 영향: SD 성능·수명·미삽입 실패를 다뤄야 하며 부팅 이미지 기록은 여전히 필요할 수 있다.
- 재검토: 실제 SD 접근이 불가능하거나 사용 요구가 변경된 경우.
- 변경: D014에 따라 SD rootfs의 배포판은 Nura 26.06이다. microSD ext4·내부 재파티셔닝/rootfs 설치 제외 범위는 유지한다.

## D004. One UI 복귀 보장 범위

- 상태: 사용자 확인 후 채택.
- 선택: 정상 이미지 복원과 순정 One UI 재설치 경로를 필수 검증한다. 개인 데이터는 백업하며 초기화 가능성을 수용한다.
- 영향: 기기 고유 데이터와 firmware revision을 보존한다. Knox의 완전한 원복은 약속하지 않는다.
- 재검토: 복구 패키지·Download Mode·도구 호환성을 검증하지 못하면 기기 기록 관문을 통과하지 못한다.

## D005. Debian 호스트와 제한적 HAL

- 상태: 사용자 확인 후 채택.
- 선택: systemd가 host PID 1, Docker는 host에서 실행한다. 표준 Linux를 우선하고 필요한 기능에만 Android HAL/LXC를 허용한다.
- 영향: Android init은 container PID 1일 수 있다. lmkd·Zygote·system_server는 기본 실행하지 않는다. legacy kernel LMK는 별도 조사한다.
- 재검토: HAL이 광범위한 Android framework·전역 정책을 요구하면 비용과 목표 영향을 다시 평가한다.
- 변경: D014에 따라 호스트 배포판은 Nura 26.06으로 변경한다. systemd host PID 1·호스트 Docker·제한적 HAL 경계는 유지한다.

## D006. 터치 Xfce와 소형 서버 겸용

- 상태: 사용자 확인 후 채택.
- 선택: Xfce/X11·화면 키보드·회전·배율을 보완하고 ARM64 웹/API 컨테이너를 기준 부하로 사용한다.
- 영향: 초기 GPU 가속 없이 GUI를 검증할 수 있으나 앱별 제스처와 GPU 가속은 별도 과제다. 서비스 실행 중 절전 제한이 필요하다.
- 재검토: Xorg/display 경로의 구조적 장애 또는 사용자 UI 요구 변경.

## D007. 전체 기능 추적

- 상태: 사용자 확인 후 채택.
- 선택: 화면·터치·Wi-Fi·Bluetooth 우선, GPU·audio·camera·sensors·GPS·power 등 전체 기능을 후속 지원표에 유지한다.
- 영향: 우선 기능 완료와 프로젝트 전체 완료를 구분한다. 특정 기능의 성공 시점을 보장하지 않는다.
- 재검토: 실제 미탑재 기능은 근거와 함께 해당 없음으로 변경한다.

## D008. 분해 없는 디버깅

- 상태: 사용자 확인 후 채택.
- 선택: USB·recovery·pstore·로그를 사용한다. UART·테스트 포인트·납땜은 제외한다.
- 영향: 매우 초기 부팅 실패의 관측 한계가 있을 수 있다.
- 재검토: 사용자가 하드웨어 디버깅 범위를 명시적으로 확장한 경우.

## D009. 학습과 문서·인수인계

- 상태: 사용자 확인 후 채택.
- 선택: C 가능·커널 입문, 하루 약 2시간. 여러 Markdown에 상세 계획을 나누고 AGENTS·HANDOFF·지침·템플릿을 둔다.
- 영향: 매 실험마다 가설·관측·코드 경로·다음 행동을 남긴다. 새 에이전트 실행은 문서 준비와 별개다.
- 재검토: 사용 시간·학습 배경·협업 방식 변경.

## D010. 단계별 실행과 설명 보고서

- 날짜: 2026-09-29. 상태: 사용자 확인 후 채택.
- 배경: 기존 문서를 실제 구현 인터페이스로 구체화하면서 커널 학습을 유지한다.
- 선택: 사용자가 단계를 선택하면 그 안의 정해진 명령을 실행하고 목적·관측·의미·한계·다음 행동을 보고한다. 자동으로 다음 포팅 단계까지 연속 실행하지 않는다.
- 영향: probe의 원본·정규화 사실·설명 보고서를 연결한다. partial과 unavailable을 숨기지 않고 실측과 추론을 구분한다.
- 재검토: 사용자가 연속 실행이나 명령별 수동 실습을 요구한 경우.

## D011. 조사·빌드 도구와 데이터 계약 v1

- 날짜: 2026-09-29. 상태: 설계 채택. 2026-09-30 수집기 구현·합성 검증, 빌드 도구 미구현.
- 선택: Python 3.11 이상·표준 라이브러리 CLI. Windows/Linux 공통 수집·보고서, Linux/WSL 소스 준비·빌드. source lock·recipe·kernel bundle의 JSON v1을 정의한다.
- 범위: 이번에는 조사·빌드 관리를 먼저 확정한다. initramfs 내부 구현·rootfs 생성·boot 조립·flash 도구는 다음 설계 대상이다.
- 영향: 정확한 SHA·도구 체인·기기 대응 근거가 미확정이면 draft로 보관하고 실행하지 않는다. 빌드 성공·파일 무결성·실기기 시험은 별도 상태다.
- 세부 기준: [수집기](design/01-device-collector.md), [빌드 관리](design/02-build-artifacts.md), [데이터 계약](design/03-data-contracts.md).
- 재검토: 실제 ROM source·toolchain 요구가 계약으로 표현되지 않으면 관측 근거와 함께 계약·reader·fixture를 같이 변경한다.
- 변경: D014 이후 이미지·패키지 생성은 pmbootstrap/Nura 표준 도구를 우선한다. 기존 수집기·JSON v1 구현은 유지하며 미구현 자체 빌드 엔진의 우선 구현 계획은 대체한다. 연동에 필요한 계약 변경은 별도 설계한다.

## D012. exec-out 형식 검사와 식별 이전 root 제한

- 날짜: 2026-09-30. 상태: 구현 반영.
- 근거: [ADB client 구현](https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/client/commandline.cpp)은 exec-out raw stream을 stdout으로 복사하고 원격 종료 frame 없이 client 성공을 반환한다. host stderr 분리가 remote stderr 분리까지 보장하지 않는다.
- 선택: binary remote_exit_code는 null, gzip CRC·길이·DT frame 검사로 읽기 결과를 판정한다. 고정 wrapper marker로 부재·권한 제한을 구분한다. gzip 압축 해제는 16MiB로 제한한다.
- 식별 관문: root 허용 여부와 관계없이 정확한 모델·코드명이 관측되기 전 su를 요청하지 않는다. 이후 권한 부족 읽기에만 기존 adapter를 사용한다.
- 검증: CRC·부분 파일·DT cell·비 UTF-8 원본·미확인 모델에서 root 미호출을 합성 응답으로 시험했다. 실제 su와 Android 전송 동작은 미검증이다.
- 영향: 첫 설계의 'stderr 분리'는 ADB client 기준으로 명확히 정정했다. 수집 사실과 실제 기기 동작의 구분은 유지한다.

## D013. One UI를 포팅 기준 ROM으로 선택

- 날짜: 2026-10-30, Asia/Seoul. 상태: 사용자 선택에 따라 계획 채택, 실기기 전환·검증 미실행. D001의 기준 ROM과 D004의 복구 절차를 구체화한다.
- 배경: 사용자는 SM-T500 순정 패키지를 제공했고 One UI를 다시 설치해 포팅 기준으로 삼겠다고 했다. 로컬 `T500XXS8CXG1` 패키지의 구성·내장 MD5·SHA-256·boot header·커널 설정을 정적으로 확인했다.
- 선택: One UI 정상 부팅을 검증한 뒤 해당 이미지·kernel/vendor·DT·설정을 기준으로 사용한다. LineageOS 설치 패키지·이미지 확보와 재설치를 필수 선행 조건으로 두지 않는다. 공개 LineageOS 소스는 필요할 때 비교 자료로 사용할 수 있다.
- 영향: 기기의 현재 OS가 One UI로 바뀌었다고 가정하지 않는다. 전환 전 모델·CSC·bootloader 리비전·백업 및 롤백 조건을 확인하고, 전환 후 기준 조사를 새로 수행한다. 기기 고유 데이터 보호와 정상 이미지 복원·One UI 재설치 검증은 유지한다.
- 구현 영향: 제공 순정 커널은 4.19.157이며 내장 설정에서 DEVTMPFS·PID_NS·CGROUP_PIDS가 꺼져 있다. 대응 Samsung 소스·toolchain을 확보하고 Debian/Docker용 설정을 보완한다. REA 분석 결과는 소스 재현·실기기 기능 검증을 대체하지 않는다.
- 재검토: 제공 패키지가 실제 기기 리비전과 호환되지 않거나 대응 소스·필수 기능의 재현이 막히면 근거와 대체 기준을 기록한다.
- 관련 증거: [제공 패키지 정적 조사](firmware/T500XXS8CXG1.md), [복구 지침](03-backup-and-recovery.md), [커널 재현](06-kernel-porting.md).
- 역할 구체화: D014 이후 One UI는 기기 관측·firmware 출처·복구 기준이며 포팅할 호스트 OS는 Nura 26.06이다. One UI 순정 kernel을 Nura 기본 kernel로 상속하지 않는다.

## D014. Nura 26.06 공통 기반과 SM-T500 지원의 분리

- 날짜: 2026-10-30, Asia/Seoul. 상태: 사용자 명시 선택으로 채택. N1에서 metadata APK·rootfs 준비물을 생성/검사했고 N2에서 공식 LTS·시험 DT·initramfs 연결과 install을 검증했다. N1 install 종료 1과 N2 종료 0을 구분하며 boot.img·기기 설치는 미실행이다. N2 전체는 부분 완료다.
- 배경: 사용자는 Nura 26.06 기본 이미지를 기반으로 포팅하고 기존 Tab A7 postmarketOS 포트에서 필요한 디바이스 정보 등만 가져오도록 지시했다.
- 선택: 공식 v26.06/aarch64 패키지·기본 rootfs와 pmbootstrap/Nura 표준 initramfs·패키징을 사용한다. SM-T500 전용 deviceinfo·DT·kernel fragment·firmware·초기화 변경을 검증한 출처와 함께 따로 관리한다. 기존 prebuilt/rootfs·기본 계정·배포판 서비스·오래된 kernel/config·설치 절차는 통째로 승계하지 않는다.
- 커널: Nura 26.06의 유지되는 mainline/LTS와 systemd/Docker 호환성을 우선한다. 현재 고정 pmaports의 generic LTS 6.18.35는 조사 후보이며 실제 SoC/보드 지원·최종 설정 확인 후 확정한다. 기존 포트 4.19.300/6.10 또는 위키 버전 번호를 곧바로 새 기준으로 삼지 않는다.
- 대체·유지: D001·D002의 제조사 커널/Debian 12 우선, 자체 initramfs·debootstrap 기본 구현을 대체한다. D005의 호스트 배포판을 Nura로 변경하며 systemd PID 1·Docker·제한적 HAL은 유지한다. D003·D004·D006~D010의 microSD·복구·Xfce·기능·학습·단계별 실행 범위는 유지한다. D011의 미구현 빌드 엔진은 pmbootstrap 연동 위주로 재검토한다.
- 영향: 호스트 패키지는 Alpine/apk 기반이다. 기존 순정 자료와 REA 분석은 DT/장치/firmware/서비스 관계 검증에 사용한다. 내부 userdata rootfs 설치·부트로더/PIT 변경·다른 모델 이미지 사용은 포함하지 않는다.
- 초기 기준 입력: pmaports `v26.06`의 `2a8621d64d91647f7362eac59e7cdc091ff2bba8`을 읽기 전용으로 확인했다. 도구 버전·APK 명세·이미지 해시가 추가되어야 재현 가능한 실행 세트가 된다.
- 재검토: 선택 kernel의 SM-T500 지원 부족, 26.06 패키지/도구 호환 문제, microSD 경로의 구체적 장애, 호스트 기능 요구 변경 또는 릴리스 지원 종료. 기기 범위를 조용히 넓히거나 edge/다른 배포판으로 자동 전환하지 않는다.
- 관련 문서: [실행 계획](14-nura-26.06-port-plan.md), [기존 포트 평가](research/postmarketos-gta4l.md), [검증 기준](11-validation-and-milestones.md).

## D015. 공식 LTS 바이너리와 SM-T500 DT의 오프라인 평가

- 날짜: 2026-10-30, Asia/Seoul. 상태: D014 범위의 N2 평가 세트에 채택, 실기기 kernel 확정·N2 전체 합격은 아님.
- 배경: 고정 공식 LTS 6.18.35 config에 SM6115·SD·USB와 주요 systemd/container 옵션이 있고 QUSB2 PHY는 모듈이다. N1의 mkinitfs 실패를 실제 kernel/flavor로 해소할 수 있었다.
- 선택: 공식 `linux-postmarketos-lts=6.18.35-r0` APK·모듈을 사용하고, 같은 Linux 버전의 공통 DTSI에 순정 자료로 확인한 SD·USB 연결 후보를 표현한 `dtb-samsung-gta4lwifi`를 별도 빌드한다. 기기 패키지 0.2-r0이 두 버전을 고정하고 PHY를 initramfs에 넣는다.
- 이유·대안: 기존 포트 kernel/config 전체나 LTE 통합 DT를 가져오지 않고 공식 기준에서 보드 지원 공백을 관측한다. kernel 코드 변경 필요성이 드러나면 별도 고정 source/patch 세트로 로컬 재빌드한다.
- 영향: install·mkinitfs 성공과 부팅 성공을 구분한다. 공식 APK의 생산자 commit은 `-dirty`로 정확한 source commit·동일 빌드 재현은 미검증이다. 설치 config·release·APK/모듈 해시·저장소 신뢰 경로를 보존한다. DT의 upstream GPU schema 진단·메모리/DT 선택·SD 실패 정책이 남아 `generate_bootimg=false`를 유지한다.
- 제외·재검토: firmware·보정 데이터·LTE 서비스·근거 없는 boot offset을 도입하지 않는다. Wi-Fi의 공유 무선 의존성은 별도 조사한다. 실제 부품/DT 선택 불일치, SD·USB driver 또는 kernel config 부족, 정확한 kernel 재현 필요가 확인되면 이 세트를 재검토한다.
- 검증: DT·기기 APK 빌드·install 종료 0, initramfs PHY/모듈 대응·383개 패키지의 오프라인 신뢰 경로 검사 완료. 실기기·복구 시험 미실행. [N2 실행 기록](research/nura-n2-dt-2026-10-30.md)에 명령·해시·제한을 연결한다.

## D016. 전체 삼성 펌웨어를 제외한 Git 게시

- 날짜: 2026-10-30, Asia/Seoul. 상태: 사용자의 조건부 커밋·푸시 요청에 따라 채택.
- 배경: 사용자는 삼성 펌웨어의 게시 가능성을 자세히 확인하고 문제가 있으면 제외해 푸시하도록 지시했다. 공식 모바일 EULA에서 전체 패키지의 공개 재배포 권한을 확인하지 못했고 AP·CSC/HOME_CSC는 GitHub 일반 Git 파일 제한도 넘는다.
- 선택: 순정 원본·추출 payload·비공개 조사 자료·이미지/APK/kernel/모듈·개인 키·로그는 로컬에 보존하고 Git에서 제외한다. 설명·출처·해시·분석 요약과 출처/SPDX를 유지한 포팅 소스만 검사 후 게시한다.
- 영향: 새 checkout에는 펌웨어·N1/N2 바이너리가 없으며 같은 PC/WSL 자료에 별도 접근해야 한다. `.gitignore` 외에도 index·도달 가능한 이력·실제 staged 내용을 검사한다. LFS/Release로 우회 게시하지 않는다.
- 재검토: 특정 파일의 재배포를 허용하는 명시적 라이선스와 고지/배포 조건이 확보된 경우 파일별로 재검토한다. 전체 펌웨어에 오픈소스 라이선스가 적용된다고 추정하지 않는다.
- 근거·범위: [게시 검토](firmware/redistribution-review-2026-10-30.md). 관할별 위법성을 일괄 단정하는 법률 판정과 이번 저장소의 게시 결정을 구분한다.

## 신규 결정 양식

~~~text
Dxxx. 제목
날짜·시간대 / 상태 / 대체하는 결정:
배경과 확인한 증거:
고려한 선택지:
선택과 이유:
커널·사용자 공간·기기 복구·학습에 미치는 영향:
검증 방법 / 재검토 조건:
관련 문서·실험:
~~~
