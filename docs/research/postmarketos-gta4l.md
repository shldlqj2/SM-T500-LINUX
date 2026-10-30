# postmarketOS 기존 gta4l 포트 검토

2026-10-30, Asia/Seoul. 사용자는 새 Debian 포트를 조립하는 대신 기존 postmarketOS 포트를 보완하는 방향과 네이티브 실행·Docker 가능 여부를 질문했다. 이번 범위는 공개 문서·고정 commit의 소스 설정을 읽는 정적 비교다. 배포판 전환·빌드·다운로드 이미지 설치·기기 변경은 수행하지 않았다. 기존 미커밋 변경과 제공 순정 자료는 보존했다.

이 문서는 선택 전 비교 기록이다. 이후 사용자는 [D014](../decisions.md)와 [Nura 26.06 포팅 계획](../14-nura-26.06-port-plan.md)을 채택했다. 현재는 공식 26.06 공통 기반을 사용하고 기존 포트의 필요한 기기 정보·코드만 선별 이식한다. 아래의 '전환 검토'·기존 Debian 목표 설명은 검토 시점의 맥락이며 최신 실행 계획이 아니다.

## 네이티브 실행과 컨테이너

postmarketOS(현재 명칭 Nura)는 Alpine Linux 기반의 독립 Linux 배포판이다. 기기가 Linux kernel을 부팅하고 일반 Linux 사용자 공간을 호스트로 실행한다. 제조사 downstream kernel을 사용하는 경우에도 이 실행 방식은 네이티브 Linux에 해당하며, 메인라인 여부·하드웨어 완성도·Docker 지원 여부와 구분한다. [공식 소개](https://nura.eco/), [포트 분류](https://docs.postmarketos.org/pmaports/main/packaging/device-categorization.html)

Alpine에는 aarch64용 Docker Engine/CLI 패키지가 있다. 실제 기기에서 실행하려면 kernel namespace·cgroup·네트워크·스토리지 기능 및 서비스 구성을 확인해야 한다. 일반 ARM64 컨테이너는 후보가 되지만 amd64 전용 이미지는 에뮬레이션 없이 직접 실행되지 않는다. [Alpine Docker 패키지](https://pkgs.alpinelinux.org/package/edge/community/aarch64/docker), [Docker 요구사항](https://docs.docker.com/engine/install/binaries/), [컨테이너 아키텍처](https://docs.docker.com/build/building/multi-platform/)

호스트를 postmarketOS로 바꾸면 Debian/apt 대신 Alpine/apk 기반으로 바뀐다. systemd 지원도 존재하므로 postmarketOS가 항상 OpenRC만 사용한다고 가정하지 않는다. 목표 host PID 1과 선택한 포트의 실제 조합은 빌드·부팅 단계에서 검증한다. [v26.06 공식 발표](https://nura.eco/blog/2026/06/21/v26.06-release/)

## 사용자 제공 위키의 상태

[기기 위키](https://wiki.nura.eco/wiki/Samsung_Galaxy_Tab_A7_(samsung-gta4l))는 SM-T500/gta4lwifi와 LTE 변형을 함께 기재한다. wifi 별도 문서는 이 통합 페이지로 redirect된다. 이는 다른 모델의 이미지·DT를 SM-T500에 기록할 근거가 아니다.

위키의 개발 기능표는 화면·터치·Wi-Fi·Bluetooth·3D 등을 동작, 배터리·오디오를 부분 동작, 카메라를 미지원으로 표기한다. **위키 자체가 이 표는 전체 개발 현황이며 배포 Google Drive 이미지에서 바로 동작하는 기능표가 아니라고 명시한다.** mainline 배포 이미지에는 Himax 터치 변형 제약도 적혀 있고 하단 부품별 표와의 차이도 있어, 우리 실기기의 기능 상태로 옮기지 않는다.

위키는 아직 pmaports에 패키징되지 않았다고 선언한다. 설치 예시는 내부 userdata rootfs를 사용하고 SD 부팅은 계획으로 설명한다. 기존 프로젝트의 microSD rootfs·내부 변경 최소화와 차이가 있으므로 해당 설치 예시를 실행하지 않았다. 기존 포트의 U-Boot 관련 표기도 현재 프로젝트의 부트로더 변경 허가로 해석하지 않는다.

위키에는 kernel 7.2.0 표기가 있지만 아래 연결 저장소 mainline recipe는 6.10을 선언한다. 위키·저장소·배포 이미지가 같은 세트라는 근거는 아직 없으며 최신 이미지의 실제 소스 대응 확인이 필요하다.

## 연결된 소스의 고정 관측

### 배포판 릴리스와 kernel 버전 구분

사용자의 추가 질문에 따라 v26.06과 기기 포트의 관계를 재확인했다. Nura v26.06은 배포판 릴리스 번호이며 공식 발표상 Alpine 3.24 기반이다. 아래 recipe의 4.19.300·6.10 및 위키의 7.2.0은 kernel 버전으로, 이 숫자만으로 기기 이미지의 배포판 버전을 판단할 수 없다. 위키와 확인한 기기 recipe에는 배포 rootfs가 v26.06 기반이라는 명시적 근거가 없었다. 따라서 26.06 이미지로 확인됐다고 표시하지 않으며, 반대로 반드시 이전 배포판이라고 단정하지도 않는다. 실제 이미지의 os-release·패키지 저장소·빌드 채널/로그 확인이 남아 있다. 기존 기기 지원 패키지를 26.06에 이식해 사용할 수 있는지는 별도 빌드·부팅 검증 대상이다.

[LinuxForGta4l 저장소](https://github.com/LinuxForGta4l/postmarketos-packages-gta4l)의 실제 브랜치를 GitHub API로 확인했다. 현재 브랜치는 downstream과 mainline이며 `main` 경로는 API에서 404였다. 검색 도구의 과거 `main` 캐시보다 아래 고정 commit을 기준으로 한다. APKBUILD·스크립트·패치는 읽기만 했으며 source/eval/실행하지 않았다.

| 항목 | downstream | mainline |
| --- | --- | --- |
| package commit | `35b3893a62ea326fe487b0790827fc1a72717f49` | `d7fa5a483d488c11a7b4b589b9cc0fda1ed4cf0c` |
| recipe kernel 버전 선언 | 4.19.300 | 6.10 |
| kernel source | LineageOS/android_kernel_samsung_sm6115 | sm6115-mainline/linux |
| kernel source commit | `381a5549ee66fa751f632ee0840f5631274209ee` | `42b61ea7cdb9f531dd53f9e2c844a056db8978c1` |
| CONFIG_PID_NS | 비활성 | y |
| CONFIG_CGROUP_PIDS | 비활성 | y |
| CONFIG_CGROUPS / MEMCG | y / y | y / y |
| CONFIG_OVERLAY_FS / VETH / BRIDGE | y / y / y | y / y / y |
| CONFIG_SECCOMP_FILTER | y | y |
| CONFIG_NF_TABLES | 비활성 | m |

근거: [downstream config](https://github.com/LinuxForGta4l/postmarketos-packages-gta4l/blob/35b3893a62ea326fe487b0790827fc1a72717f49/linux-samsung-gta4l/config-samsung-gta4l.aarch64), [mainline config](https://github.com/LinuxForGta4l/postmarketos-packages-gta4l/blob/d7fa5a483d488c11a7b4b589b9cc0fda1ed4cf0c/linux-postmarketos-qcom-sm6115/config-postmarketos-qcom-sm6115.aarch64), [mainline recipe](https://github.com/LinuxForGta4l/postmarketos-packages-gta4l/blob/d7fa5a483d488c11a7b4b589b9cc0fda1ed4cf0c/linux-postmarketos-qcom-sm6115/APKBUILD)

downstream의 PID namespace 비활성은 일반 Docker 사용을 위해 보완해야 할 구체 항목이다. mainline config에는 주요 컨테이너 기능이 켜져 있어 Docker 목표에는 유리한 출발점으로 평가한다. 이는 설정 파일 비교에 따른 판단이며 최종 config·이미지·Docker daemon·컨테이너 네트워크/volume를 실행한 결과가 아니다.

두 브랜치의 deviceinfo는 LTE 이름을 사용하며 ramdisk offset을 `0x20000000`으로 선언한다. 제공 SM-T500 순정 이미지 header에서 읽은 `0x02000000`과 다르다. 브랜치의 의도·조립 방식·최종 boot 이미지와 실제 부트로더 해석을 확인하기 전 어느 값을 수정하거나 기록하지 않는다.

## 효율성과 다음 판단

기존 pmbootstrap·기기 패키지·firmware 패키지·mainline DTS 작업을 재사용하면 배포판 공통 기능의 자체 구현을 줄일 가능성이 크다. 따라서 기존 포트 재현·보완을 우선 평가하는 것이 합리적이다. 다만 현재 공개 자료만으로 다운로드 이미지가 SM-T500에서 Docker·화면·터치·Wi-Fi·Bluetooth·microSD를 모두 만족한다고 판단하지 않는다.

다음 판단은 최대 세 가지다.

1. 최신 mainline 이미지와 재현 가능한 source/recipe의 대응을 확인한다. 완료 조건: 실제 kernel·DT·설정·출처·해시가 연결된 세트와 미확인 목록.
2. SM-T500의 터치 변형·복구 관문·microSD 부팅 경로를 대조한다. 완료 조건: 다른 모델 이미지 혼용·내부 rootfs 설치·부트로더 변경 없이 평가 가능한 범위와 부족한 작업 확인.
3. 목표 충족 비용을 비교해 배포판 전환을 결정한다. 완료 조건: Alpine/apk 사용, host systemd·Docker·GUI·무선·저장소의 차이와 변경 범위를 결정 기록에 반영. 현재 Debian 기준의 폐기·포트 설치는 아직 실행하지 않았다.

## 로컬 증거와 실행 기록

Windows PowerShell/Python, cwd는 저장소 루트. MediaWiki API `action=parse&prop=wikitext`와 GitHub branches/tree API·고정 commit raw 파일을 urllib로 읽었다. 실행 종료 코드는 0이며 공개 recipe·config 등 소규모 파일 17개를 저장했다. kernel 소스 전체나 배포 이미지는 받지 않았다.

로그·자료는 `private/research/postmarketos-20261030/`에 있다. `gta4l-wiki.json`, `gta4lwifi-wiki.json`, `branches.json`, 브랜치별 tree·원본 파일, `source-manifest.json`이 있으며 source manifest에 commit·URL·크기·SHA-256을 기록했다. 위키 로그인 정보·배포 이미지의 기본 계정 정보는 공유 문서에 옮기지 않았다.

web 도구는 위키 차단 화면을 반환했지만 로컬 Python의 공개 MediaWiki API 조회는 성공했다. pmaports의 추정 경로와 main 브랜치의 404는 기록했으며, 이것을 전체 포트가 없다는 증거로 해석하지 않았다. 실제 사용자가 제공한 위키와 그 연결 소스를 기준으로 비교했다. REA가 필요한 비공개 바이너리 분석·실기기 검증은 이번 질문 범위에서 수행하지 않았다.
