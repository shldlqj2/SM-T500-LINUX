# 04. 개발 환경과 재현 가능한 빌드

## 역할 분리

| 환경 | 담당 |
| --- | --- |
| Windows | ADB·USB 장치 인식, 검증된 Samsung 복원 도구, 문서 작업 |
| WSL2 Ubuntu 24.04 | 소스·크로스 컴파일·이미지 분석·rootfs 생성·QEMU |
| QEMU arm64 | 커널 기초·initramfs·systemd·실패 주입 실습 |
| SM-T500 | 실제 부트로더·DT·드라이버·전원·복구 검증 |

WSL2 Ubuntu 24.04가 설치되어 있다는 사실만 확인했다. 패키지·디스크 공간·메모리·USB 접근은 미검증이다. 호스트의 docker-desktop 배포판은 태블릿 Docker 구현과 별개다.

## 사전 조사

WSL 내부 배포판 버전, CPU/RAM, 사용 가능한 디스크, Git·컴파일러·Python·QEMU 버전을 조사한다. 빌드 병렬 수는 호스트 메모리에 맞춰 정하고 첫 빌드에서 peak 메모리와 디스크 사용량을 기록한다.

대용량 커널 소스·빌드는 WSL Linux 파일시스템에 둔다. Windows 마운트 경로의 권한·대소문자·심볼릭 링크 차이를 피한다. 현재 Windows 문서 저장소와 WSL 빌드 경로는 별개이며 어떤 커밋·파일을 전달했는지 기록한다.

Orca 관리 worktree를 실제로 추가하는 경우 orca-cli 지침을 따른다. 이 문서만으로 새 worktree나 에이전트를 자동 생성하지 않는다.

## 도구군

- 소스: Git, 필요한 경우 해당 ROM의 repo manifest 도구.
- 커널 빌드: 기준 소스가 요구하는 Clang/LLVM 또는 GCC, make, bison, flex, bc, OpenSSL·ELF 개발 헤더 등.
- 이미지: 출처·커밋을 고정한 AOSP unpack_bootimg/mkbootimg/avbtool, dtc, DTBO 분석 도구.
- 사용자 공간: debootstrap 또는 mmdebstrap 중 초기에는 debootstrap, qemu-user-static/binfmt 지원, e2fsprogs, cpio, gzip, kmod.
- 가상 실습: qemu-system-aarch64, GDB, BusyBox 빌드 도구.
- 검증: shell·Git·해시 도구, 필요한 최소 lint 도구.

패키지 목록을 설치 명령으로 확정하기 전에 현재 환경과 소스 요구사항을 대조한다. 최신 Clang을 무조건 선택하지 않는다. 도구 체인 다운로드 주소·버전·해시와 라이선스를 기록한다.

## 소스 고정

각 소스마다 URL, branch, 실제 commit SHA, 하위 저장소 SHA, patch series를 기록한다. branch 이름만으로 재현 가능하다고 판단하지 않는다.

공개 최신 브랜치를 현재 기기의 대응 소스로 단정하지 않는다. ROM release 정보·빌드 manifest·커널 식별자를 연결해 기준 커밋을 확정한다. 네트워크에서 가져온 build script는 실행 전에 다운로드 대상과 외부 쓰기 동작을 읽는다.

빌드 컨테이너를 사용하는 경우 digest와 mount 경로를 기록한다. 빌드에 필요한 권한과 기기 기록 권한을 섞지 않는다. 전체 Android 빌드는 제한적 HAL 구현에 실제로 필요한 시점까지 미룬다.

## 빌드 산출물 계약

필수 항목은 build ID, 소스·도구 체인, 최종 .config, 커널 release, Image/DT/모듈 해시, build log, boot 패키징 보고서, rootfs ID다. 구체적인 이미지 계약은 [05 문서](05-boot-and-image-design.md)를 따른다.

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

QEMU에서 성공한 사용자 공간 구성도 실제 기기의 4.19 커널에서 재검증한다. QEMU 성공은 SM-T500의 패널·무선·전원 지원 증거가 아니다.

## 완료 조건

- WSL 환경 및 도구 체인 명세가 있다.
- 별도 소스·산출물 경로가 정해지고 빌드 로그가 보존된다.
- QEMU에서 직접 만든 initramfs가 실행된다.
- 기준 커널의 소스와 설정을 어떤 방식으로 재현할지 확정했다.
- 어떤 빌드 도구도 자동으로 기기에 기록하지 않는다.

## 참고

- [ARM64 커널 부팅](https://docs.kernel.org/arch/arm64/booting.html)
- [Linux Kbuild 문서](https://docs.kernel.org/kbuild/index.html)
- [AOSP boot image header](https://source.android.com/docs/core/architecture/bootloader/boot-image-header)
