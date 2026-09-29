# 06. 커널 재현과 단계적 포팅

## 기본 전략

정상 Android 커널을 재현한 뒤 Debian용 변경을 별도 patch/config 조각으로 추가한다. 처음부터 커널을 최소화하거나 최신 버전으로 올리지 않는다. 소스·설정·컴파일러·DT·모듈이 함께 맞아야 기기 지원을 재현할 수 있다.

현재 설치된 커널 버전과 소스는 미확인이다. 조사한 공개 LineageOS lineage-23.2 브랜치의 Makefile은 4.19.325를 표기하지만 이것을 실기기 버전으로 사용하지 않는다.

## 기준 소스 확정

1. 현재 ROM build와 kernel release·build string을 확보한다.
2. ROM manifest·release 자료에서 대응 source SHA를 찾는다.
3. base config, device config, vendor modules와 toolchain을 연결한다.
4. source provenance와 실제 .config를 비교한다.
5. 일치하는 소스가 없으면 검증 가능한 공개 SM-T500 ROM을 기준점 후보로 선정한다.
6. [복구](03-backup-and-recovery.md)를 확보한 뒤 기준 ROM으로 전환하고 조사·회귀검사를 다시 수행한다.

최신 커널 브랜치와 현재 vendor를 조합해 우연히 부팅하는 상태를 재현 가능한 기준으로 취급하지 않는다. 루팅 패치는 원본 kernel/ramdisk 변경과 구분한다.

## 설정 묶음

| 묶음 | 확인할 기능·대표 심볼 | 통과 증거 |
| --- | --- | --- |
| baseline | 원본 defconfig + device fragment | Android 재부팅·핵심 기능 유지 |
| native boot | BLK_DEV_INITRD, DEVTMPFS, TMPFS, MMC·host, EXT4_FS | initramfs·SD 접근 |
| observability | PSTORE, PSTORE_RAM, KALLSYMS, 선택적 DYNAMIC_DEBUG | 유효한 로그와 symbol |
| systemd | CGROUPS, INOTIFY_USER, SIGNALFD, TIMERFD, EPOLL, FHANDLE, UNIX | PID 1·udev·서비스 |
| container | namespace 하위 옵션, MEMCG, CGROUP_PIDS, CFS_BANDWIDTH, SECCOMP_FILTER, VETH, BRIDGE, netfilter, OVERLAY_FS | 제한·네트워크·저장소 시험 |
| compatibility | 실제 필요한 Binder·binderfs·기타 vendor 인터페이스 | 최소 HAL 서비스 |
| memory/power | ZRAM, 지원 압박 지표, thermal·cpufreq·PM | OOM·온도·절전 결과 |

심볼 이름·의존성은 해당 4.19 tree의 Kconfig를 기준으로 확인한다. 최신 upstream 문서의 옵션을 무조건 추가하지 않는다. fragment에 줄을 넣었다고 최종 설정이 켜졌다고 판단하지 않고 merge 후 최종 .config를 검사한다.

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

1. 원본 설정으로 빌드하고 Android에서 기준 기능 재검증.
2. 진단 기능 추가 및 로그 회수 검증.
3. Debian boot·systemd 필수 기능 추가.
4. 컨테이너 기능 추가.
5. 기기별 하드웨어·사용자 공간 적응.
6. 사용하지 않는 Android 정책·기능 정리.

Android baseline을 검증하기 전에 LMK·SELinux·Binder·vendor hook을 일괄 제거하지 않는다. Debian용 프로필에서 실제 필요성과 전역 영향을 조사한 뒤 최소 변경한다. '일단 모든 보안 기능 끄기'를 상시 설정으로 사용하지 않는다.

## 드라이버 디버깅 순서

DT enabled 상태 → compatible match → 부모 bus·clock·regulator → probe 반환값 → firmware → IRQ/DMA → 장치 노드 → userspace 순서로 확인한다.

deferred probe는 드라이버 자체 실패일 수도 있지만 공급자 미준비 때문일 수 있다. devices_deferred 등 해당 커널이 제공하는 인터페이스와 로그를 사용한다. 없는 최신 debugfs 항목을 전제로 도구를 만들지 않는다.

printk·dynamic debug를 먼저 사용하고 필요한 범위에서 ftrace를 켠다. KASAN·lockdep·광범위 DEBUG 옵션은 RAM·타이밍을 바꾸므로 별도 debug 이미지로 운영한다. debug 성능 수치를 정상 이미지 성능으로 보고하지 않는다.

한 번에 한 원인을 검증한다. 같은 실패가 반복되면 '가설·관측·반증·다음 가설'을 기록하고 정상 세트로 되돌린다. git bisect는 동일 source 계열과 재현 가능한 검사일 때 사용한다.

## 완료 조건·산출물

기준 source/toolchain 명세, 원본·변경 .config diff, 독립 patch series, 커널·모듈 세트, Android baseline 회귀검사, Debian 부팅·컨테이너 검사 기록을 남긴다. 커널 업그레이드는 별도 [메인라인 계획](13-mainline-roadmap.md)에서 수행한다.

## 참고

- [기준 Makefile](https://github.com/LineageOS/android_kernel_samsung_sm6115/blob/lineage-23.2/Makefile)
- [bengal defconfig](https://github.com/LineageOS/android_kernel_samsung_sm6115/blob/lineage-23.2/arch/arm64/configs/vendor/bengal-perf_defconfig)
- [기기 config](https://github.com/LineageOS/android_kernel_samsung_sm6115/blob/lineage-23.2/arch/arm64/configs/vendor/gta4l-common.config)
- [systemd 252 요구사항](https://github.com/systemd/systemd/blob/v252/README)
