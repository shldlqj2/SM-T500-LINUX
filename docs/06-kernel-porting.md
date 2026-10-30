# 06. 커널 재현과 단계적 포팅

## 기본 전략

[D014](decisions.md)에 따라 Nura 26.06과 systemd/Docker에 호환되는 유지되는 mainline/LTS를 기준으로 SM-T500 지원을 추가한다. [포팅 계획](14-nura-26.06-port-plan.md)의 공식 generic LTS recipe는 초기 조사 후보이며 실제 kernel은 SoC·보드·패키지 요구를 대조한 뒤 확정한다. 소스·설정·컴파일러·DT·모듈이 함께 맞아야 기기 지원을 재현할 수 있다.

현재 실기기에 설치된 커널 버전과 소스는 미확인이다. 조사한 공개 LineageOS lineage-23.2 브랜치의 Makefile은 4.19.325를 표기하지만 이것을 실기기 버전으로 사용하지 않는다.

[N2 오프라인 평가](research/nura-n2-dt-2026-10-30.md)에서는 공식 LTS 6.18.35-r0 APK·대응 모듈과 로컬 시험 DT를 연결하고 install·표준 initramfs 생성에 성공했다. 설치 config·release·PHY vermagic·해시를 검사했으나 kernel 전체 로컬 컴파일과 생산자 source commit의 재현은 미실행이다. DT binding의 upstream GPU 진단·boot 계약이 남아 있어 N2 전체 합격이나 기기 지원 완료로 표시하지 않는다.

2026-10-30 [D013](decisions.md)의 One UI는 하드웨어 관측·복구 기준으로 사용한다. [제공 순정 패키지](firmware/T500XXS8CXG1.md)의 커널은 `4.19.157-perf-26272441-abT500XXS8CXG1`이고 내장 IKCONFIG를 확보했다. DEVTMPFS·PID_NS·CGROUP_PIDS 등의 비활성은 참고 관측값이며 이 설정을 Nura 기준으로 복제하지 않는다. 기기 재설치·런타임 조사는 미실행이고 LineageOS 재설치는 필수 조건이 아니다.

## 기준 소스 확정

1. 공식 Nura v26.06 pmaports SHA·kernel recipe·source·toolchain·패키지 요구를 고정한다.
2. SM6115 공통 지원과 SM-T500 보드·실제 부품에 부족한 driver/DT를 조사한다.
3. 기존 Tab A7 포트와 순정 자료에서 필요한 정보·패치만 출처/라이선스와 함께 선택한다.
4. Nura base config에 작은 device fragment·patch를 추가하고 최종 .config·DT·modules의 대응을 검사한다.
5. 정적 kernel/initramfs/boot 검사를 먼저 수행하고 [복구](03-backup-and-recovery.md) 관문 후 실기기에서 검증한다.
6. 부족한 지원이 발견되면 원인을 기록하고 kernel 후보 또는 필요한 패치를 비교한다. 오래된 kernel 전체로 자동 회귀하지 않는다.

최신 커널 브랜치와 현재 vendor를 조합해 우연히 부팅하는 상태를 재현 가능한 기준으로 취급하지 않는다. 루팅 패치는 원본 kernel/ramdisk 변경과 구분한다.

## 설정 묶음

| 묶음 | 확인할 기능·대표 심볼 | 통과 증거 |
| --- | --- | --- |
| baseline | Nura kernel recipe/config + 검토한 device fragment | 최종 설정·DT·모듈 대응 및 정적 검사 |
| native boot | BLK_DEV_INITRD, DEVTMPFS, TMPFS, MMC·host, EXT4_FS | initramfs·SD 접근 |
| observability | PSTORE, PSTORE_RAM, KALLSYMS, 선택적 DYNAMIC_DEBUG | 유효한 로그와 symbol |
| systemd | CGROUPS, INOTIFY_USER, SIGNALFD, TIMERFD, EPOLL, FHANDLE, UNIX | PID 1·udev·서비스 |
| container | namespace 하위 옵션, MEMCG, CGROUP_PIDS, CFS_BANDWIDTH, SECCOMP_FILTER, VETH, BRIDGE, netfilter, OVERLAY_FS | 제한·네트워크·저장소 시험 |
| compatibility | 실제 필요한 Binder·binderfs·기타 vendor 인터페이스 | 최소 HAL 서비스 |
| memory/power | ZRAM, 지원 압박 지표, thermal·cpufreq·PM | OOM·온도·절전 결과 |

심볼 이름·의존성은 선택한 kernel tree의 Kconfig를 기준으로 확인한다. 순정 4.19나 기존 6.10 설정을 이름만 같다는 이유로 복사하지 않는다. fragment에 줄을 넣었다고 최종 설정이 켜졌다고 판단하지 않고 merge 후 최종 .config를 검사한다.

공개 bengal 설정에는 cgroups·seccomp·OverlayFS·PSI·KGSL 등이 존재한다. CONFIG_CMDLINE에 cgroup_disable=pressure도 보이므로 컴파일 설정과 /proc/cmdline, 런타임 인터페이스를 함께 확인한다. PSI 동작을 일반 4.19 지원 여부만으로 추정하지 않는다.

## 빌드·모듈 일치

- 기준 toolchain과 vendor build recipe를 우선 사용한다.
- 외부 audio/WLAN 모듈의 build target·source revision·심볼 의존성을 포함한다.
- modules_install의 대상 rootfs와 /lib/modules/<release>를 기록한다.
- depmod 결과·vermagic·CONFIG_MODVERSIONS·Module.symvers 대응을 검사한다.
- unknown symbol 또는 invalid module format을 강제 옵션으로 우회하지 않는다.
- LOCALVERSION 변경은 구분에 유용하지만 vendor 모듈 ABI에 영향을 주므로 전체 세트를 다시 만든다.
- 재현은 우선 기능·설정·출처 재현이다. 시간·경로가 포함된 빌드의 바이트 동일성을 별도 검증 없이 약속하지 않는다.

## 변경 순서

1. Nura 기준 recipe·필요한 SM-T500 device 변경으로 빌드하고 최종 설정·DT·모듈 검사.
2. 진단 경로·Nura initramfs·SD 의존성을 초기 실험 세트로 검증.
3. Nura boot·systemd 필수 기능 검증.
4. 컨테이너 기능 추가.
5. 기기별 하드웨어·사용자 공간 적응.
6. 사용하지 않는 Android 정책·기능 정리.

순정 baseline은 하드웨어 관측·복구 기준으로 유지한다. 선택한 Nura kernel에 Android용 LMK·Binder·vendor hook을 필요 없이 추가하지 않는다. HAL 의존성이 확인된 기능만 별도로 검토하고 보안 기능의 일괄 비활성화를 상시 설정으로 사용하지 않는다.

## 드라이버 디버깅 순서

DT enabled 상태 → compatible match → 부모 bus·clock·regulator → probe 반환값 → firmware → IRQ/DMA → 장치 노드 → userspace 순서로 확인한다.

deferred probe는 드라이버 자체 실패일 수도 있지만 공급자 미준비 때문일 수 있다. devices_deferred 등 해당 커널이 제공하는 인터페이스와 로그를 사용한다. 없는 최신 debugfs 항목을 전제로 도구를 만들지 않는다.

printk·dynamic debug를 먼저 사용하고 필요한 범위에서 ftrace를 켠다. KASAN·lockdep·광범위 DEBUG 옵션은 RAM·타이밍을 바꾸므로 별도 debug 이미지로 운영한다. debug 성능 수치를 정상 이미지 성능으로 보고하지 않는다.

한 번에 한 원인을 검증한다. 같은 실패가 반복되면 '가설·관측·반증·다음 가설'을 기록하고 정상 세트로 되돌린다. git bisect는 동일 source 계열과 재현 가능한 검사일 때 사용한다.

## 완료 조건·산출물

기준 source/toolchain 명세, Nura 원본·변경 .config diff, 출처가 있는 독립 patch series, kernel·DT·모듈 세트, Nura 부팅·컨테이너 검사 기록을 남긴다. 순정 자료와의 장치 대응 및 업데이트 정책은 [메인라인 계획](13-mainline-roadmap.md)에서 관리한다.

## 참고

- [기준 Makefile](https://github.com/LineageOS/android_kernel_samsung_sm6115/blob/lineage-23.2/Makefile)
- [bengal defconfig](https://github.com/LineageOS/android_kernel_samsung_sm6115/blob/lineage-23.2/arch/arm64/configs/vendor/bengal-perf_defconfig)
- [기기 config](https://github.com/LineageOS/android_kernel_samsung_sm6115/blob/lineage-23.2/arch/arm64/configs/vendor/gta4l-common.config)
- [Nura generic kernel](https://docs.nura.eco/pmaports/main/packaging/kernel-packages/generic-kernel-packages.html)
- [systemd v261 요구사항](https://github.com/systemd/systemd/blob/v261/README): 실제 Nura 패키지·패치와 대조한다.
