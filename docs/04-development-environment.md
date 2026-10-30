# 04. 개발 환경과 재현 가능한 빌드

## 역할 분리

| 환경 | 담당 |
| --- | --- |
| Windows | ADB·USB 장치 인식, 검증된 Samsung 복원 도구, 문서 작업 |
| Linux 빌드 환경(우선 WSL2 Ubuntu 24.04 평가) | pmbootstrap·패키지/커널 빌드·이미지 분석·rootfs 생성·QEMU |
| QEMU arm64 | 커널 기초·initramfs·systemd·실패 주입 실습 |
| SM-T500 | 실제 부트로더·DT·드라이버·전원·복구 검증 |

[N1 실행](research/nura-n1-rootfs-2026-10-30.md)에서 WSL2 Ubuntu 24.04·Linux ext4 작업 경로·메모리/디스크·pmbootstrap 3.12.1·mount/chroot·ARM64 QEMU user/binfmt·rootfs 패키지 설치를 검증했다. USB 기기 접근·kernel 빌드·실기기 부팅은 미검증이다. 호스트의 docker-desktop 배포판은 태블릿 Docker 구현과 별개다.

[N2](research/nura-n2-dt-2026-10-30.md)에서는 별도 WSL 작업 공간에서 DT·기기 APK 빌드·공식 LTS 설치·표준 initramfs 생성과 패키지 신뢰 경로를 검사했다. 호스트 GCC/dtc와 격리 dtschema를 사용했으며 전체 kernel 컴파일 환경의 검증으로 확대하지 않는다.

현재 빌드 기본 경로는 [Nura 26.06 포팅 계획](14-nura-26.06-port-plan.md)의 pmbootstrap/Nura 표준 도구다. 기존 [빌드·산출물 구현 설계](design/02-build-artifacts.md)와 [데이터 계약](design/03-data-contracts.md)의 출처·해시·상태 원칙을 유지하되 미구현 자체 빌드 엔진을 우선 만들지 않는다. 수집기는 Python 3.11 이상·표준 라이브러리 구현을 유지한다.

공식 pmbootstrap 문서는 WSL 동작을 공식 지원으로 보장하지 않는다. 이번에는 실제 사용한 mount/chroot/binfmt·패키지 생성 범위를 검증했다. 다른 WSL 버전·kernel 빌드·새 mount 경로의 성공까지 일반화하지 않으며 구체적 장애가 생기면 별도 Linux 환경을 평가한다.

## 사전 조사

WSL 내부 배포판 버전, CPU/RAM, 사용 가능한 디스크, Git·컴파일러·Python·QEMU 버전을 조사한다. 빌드 병렬 수는 호스트 메모리에 맞춰 정하고 첫 빌드에서 peak 메모리와 디스크 사용량을 기록한다.

대용량 커널 소스·빌드는 WSL Linux 파일시스템에 둔다. Windows 마운트 경로의 권한·대소문자·심볼릭 링크 차이를 피한다. 현재 Windows 문서 저장소와 WSL 빌드 경로는 별개이며 어떤 커밋·파일을 전달했는지 기록한다.

Orca 관리 worktree를 실제로 추가하는 경우 orca-cli 지침을 따른다. 이 문서만으로 새 worktree나 에이전트를 자동 생성하지 않는다.

## 도구군

- 소스: Git, 필요한 경우 해당 ROM의 repo manifest 도구.
- 커널 빌드: 기준 소스가 요구하는 Clang/LLVM 또는 GCC, make, bison, flex, bc, OpenSSL·ELF 개발 헤더 등.
- 이미지: 출처·커밋을 고정한 AOSP unpack_bootimg/mkbootimg/avbtool, dtc, DTBO 분석 도구.
- 사용자 공간·패키지·이미지: v26.06 pmaports와 호환되는 pmbootstrap, Nura 표준 initramfs·devicepkg·boot 패키징, apk, 필요한 qemu-user/binfmt·e2fsprogs·kmod. debootstrap/mmdebstrap은 현재 rootfs 생성 도구가 아니다.
- 가상 실습: qemu-system-aarch64, GDB, BusyBox 빌드 도구.
- 검증: shell·Git·해시 도구, 필요한 최소 lint 도구.

패키지 목록을 설치 명령으로 확정하기 전에 현재 환경과 소스 요구사항을 대조한다. 최신 Clang을 무조건 선택하지 않는다. 도구 체인 다운로드 주소·버전·해시와 라이선스를 기록한다.

## 소스 고정

각 소스마다 URL, branch, 실제 commit SHA, 하위 저장소 SHA, patch series를 기록한다. branch 이름만으로 재현 가능하다고 판단하지 않는다.

Nura v26.06의 공식 기준 SHA와 선택한 kernel·로컬 SM-T500 패치·설정을 따로 고정한다. 순정/기존 포트 자료는 모델·부품·DT·firmware 근거와 연결하며 기존 kernel/config를 자동 상속하지 않는다. 네트워크에서 가져온 build script는 실행 전에 다운로드 대상과 외부 쓰기 동작을 읽는다.

빌드 컨테이너를 사용하는 경우 digest와 mount 경로를 기록한다. 빌드에 필요한 권한과 기기 기록 권한을 섞지 않는다. 전체 Android 빌드는 제한적 HAL 구현에 실제로 필요한 시점까지 미룬다.

## 빌드 산출물 계약

전체 부팅 세트의 필수 항목은 build ID, 소스·도구 체인, 최종 .config, 커널 release, Image/DT/모듈 해시, build log, boot 패키징 보고서, rootfs ID다. 전체 이미지 관계는 [05 문서](05-boot-and-image-design.md)를 따른다. portctl v1의 kernel bundle은 [데이터 계약](design/03-data-contracts.md)에 정의된 설계이며 생성 CLI는 미구현이다. pmbootstrap으로 만든 N1/N2 관측용 자료와 구분한다.

커널 빌드와 이미지 조립, rootfs 생성, 기기 기록을 별도 명령/도구로 설계한다. 빌드 성공 후 자동 flash하지 않는다.

디렉터리는 sources, build, artifacts, private 자료를 구분한다. 이 저장소의 .gitignore는 이런 로컬 자료의 우발적 추가를 줄인다. 파일을 공개하기 전 실제 내용을 확인한다.

## QEMU 학습 환경

QEMU virt 머신용 upstream arm64 커널을 별도로 빌드한다. SM-T500 제조사 커널이 virt 머신에서 부팅할 것이라고 기대하지 않는다.

1. 작은 initramfs에서 /init 실행과 콘솔 출력.
2. /proc·/sys·/dev 준비 및 PID 1 동작.
3. 디스크 rootfs 연결과 switch_root.
4. systemd·SSH·시험 서비스 실행.
5. 잘못된 init·누락 rootfs·제한된 OOM 등 실패 실습.
6. GDB·ftrace 또는 사용할 수 있는 tracing 기능으로 코드 경로 관측.

QEMU에서 성공한 사용자 공간 구성도 선택한 SM-T500 kernel·DT·모듈에서 재검증한다. QEMU 성공은 SM-T500의 패널·무선·전원 지원 증거가 아니다. 자체 /init 실습은 학습용이며 Nura 표준 initramfs를 대체하는 기본 구현이 아니다.

## 완료 조건

- WSL 환경 및 도구 체인 명세가 있다.
- 별도 소스·산출물 경로가 정해지고 빌드 로그가 보존된다.
- 공식 Nura 기준 rootfs의 릴리스·패키지·init 경로를 정적으로 확인한다. QEMU 자체 initramfs 실습은 별도 선택 과제다.
- Nura kernel recipe와 선택한 SM-T500 변경의 출처·설정·도구 체인 대응을 확정했다.
- 어떤 빌드 도구도 자동으로 기기에 기록하지 않는다.

## 참고

- [ARM64 커널 부팅](https://docs.kernel.org/arch/arm64/booting.html)
- [Linux Kbuild 문서](https://docs.kernel.org/kbuild/index.html)
- [AOSP boot image header](https://source.android.com/docs/core/architecture/bootloader/boot-image-header)
