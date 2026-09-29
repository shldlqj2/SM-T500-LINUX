# 12. 커널 학습 계획

## 학습 방식

C의 포인터·구조체를 이해하고 커널은 입문한다는 기준이다. 하루 약 2시간을 문서·소스 읽기 30분, 실험 70분, 기록 20분으로 배분한다. 긴 빌드 대기에는 관련 코드 흐름을 읽는다.

각 주제는 질문 → 가설 → 관련 코드 → QEMU 실험 → 실기기 관측 → 설명 가능한 노트 순서로 진행한다. 문서를 많이 읽었다는 사실보다 실제 현상을 코드와 연결할 수 있는지가 기준이다.

## 학습 모듈

| 모듈 | 핵심 질문 | 코드·개념 | 실습·완료 산출물 |
| --- | --- | --- | --- |
| L0 도구 | C 파일이 커널 이미지가 되는 과정은? | compiler, linker, ELF, Make/Kbuild/Kconfig | 작은 C 코드의 ELF 분석·config 의존성 설명 |
| L1 부팅 | CPU가 커널 진입 후 /init까지 어떻게 가는가? | arm64 head.S, start_kernel, rest_init, kernel_init, initcall | QEMU 부팅 단계와 소스 흐름도 |
| L2 사용자 공간 | PID 1은 무엇을 해야 하는가? | exec, wait, signal, syscall, initramfs | 자체 /init·자식 회수·잘못된 init 실패 |
| L3 저장소 | SD의 파일을 read할 때 어떤 계층을 통과하는가? | VFS, dentry/inode, page cache, ext4, block, MMC | switch_root·파일 읽기 경로·UUID 실패 |
| L4 장치 모델 | DT 노드가 드라이버와 어떻게 연결되는가? | of_match, platform/I2C/SPI, probe, devm, deferred probe | 실제 기기 드라이버 1개 의존성 지도 |
| L5 인터럽트·동시성 | 터치 입력은 어떤 문맥에서 처리되는가? | IRQ, threaded IRQ, workqueue, mutex/spinlock | IRQ→evdev→앱 흐름과 문맥별 제약 |
| L6 메모리 | 여유 메모리가 줄면 무슨 일이 일어나는가? | page allocator, slab, reclaim, swap/zram, OOM | 제한된 압박·cgroup OOM·PSS 분석 |
| L7 프로세스·격리 | systemd와 container PID 1은 왜 공존하는가? | scheduler, namespaces, cgroups, credentials, seccomp | PID 매핑·CPU/memory 제한 실험 |
| L8 네트워크 | 컨테이너 패킷은 Wi-Fi까지 어떻게 가는가? | socket, veth, bridge, route, netfilter, driver | 구간별 패킷 관측과 DNS 실패 분리 |
| L9 그래픽·DMA | 화면과 GPU가 같은 기능인가? | DRM/KMS/fbdev, buffer, DMA, IOMMU, dma-buf | scanout·render 분리와 현재 ABI 설명 |
| L10 오디오·미디어 | 장치 노드가 있어도 녹음·카메라가 왜 실패하는가? | ALSA/ASoC, DSP, V4L2, ISP, HAL | 기능별 kernel/userspace 경계 지도 |
| L11 전원 | 화면 끄기와 system suspend는 어떻게 다른가? | runtime PM, wakeup source, cpufreq, thermal | 단계별 소비·복귀·실패 드라이버 분석 |
| L12 upstream | 기기 지원을 공통 코드에 어떻게 표현하는가? | bindings, DTS, driver reuse, review, bisect | 검증 가능한 최소 패치와 설명 |

함수·경로는 실제 학습 커널 버전에서 확인한다. upstream 최신 소스와 제조사 4.19는 파일 위치·API·backport가 다를 수 있다.

## 첫 실습 상세

### A. initramfs와 PID 1

QEMU virt에서 정적 BusyBox initramfs를 부팅한다. /init의 executable bit·interpreter 누락·잘못된 arch를 각각 바꿔 로그가 어떻게 달라지는지 본다. 정상 mount와 exec switch_root를 구현한 후 PID가 유지되는 이유를 설명한다.

### B. 설정의 실제 효과

필수 기능을 하나씩 빼거나 module로 바꿔 boot 실패와 연결한다. Kconfig에서 선택했지만 dependency 때문에 .config에 반영되지 않는 경우를 찾는다. 설정 조각·최종 설정·런타임의 세 층을 비교한다.

### C. 디바이스 probe

QEMU의 관측 가능한 장치 또는 간단한 시험 모듈에서 bind/probe 흐름을 학습한다. 실제 SM-T500에서는 터치·SD 중 접근 가능한 드라이버의 compatible·전원·IRQ를 추적한다. 실제 주소를 임의로 읽고 쓰는 실습은 하지 않는다.

### D. namespace·cgroup

PID namespace 안팎의 PID를 비교하고 제한된 프로세스 그룹에서 CPU·memory·pids 제한을 관측한다. namespace가 메모리 할당량을 제한하지 않는다는 것을 직접 확인한다.

### E. 관측 도구

dmesg·journal·strace·/proc·/sys부터 사용하고, 한 경로가 좁혀진 후 ftrace·dynamic debug·GDB를 도입한다. 모든 tracing을 한꺼번에 켜서 타이밍을 바꾸지 않는다.

## 위험한 실습의 장소

커널 panic·잘못된 locking·메모리 오류·OOM·파일시스템 손상은 QEMU와 폐기 가능한 이미지에서 먼저 수행한다. 실기기에서는 필요한 최소 재현만 하고 정상 이미지·로그 회수 경로를 확보한다. 일부러 충전 보호나 thermal 한계를 끄는 실습은 하지 않는다.

## 주간 노트 양식

~~~text
주제 / 학습 커널 버전·SHA:
이번에 답하려는 질문:
사전 가설:
읽은 함수·구조체·호출 경로:
사용한 실험·환경·변경:
실제 로그와 관측:
가설과 다른 부분:
커널 책임 / 사용자 공간 책임:
SM-T500 포팅에 적용한 점:
아직 설명하지 못하는 점 / 다음 실험:
~~~

매주 한 번 최근 수정한 코드 경로를 다른 사람에게 설명하듯 정리한다. 함수 이름 목록보다 데이터·제어 흐름, 오류가 발생하는 위치와 이유를 보여 준다.

## 참고 자료

- [커널 개발 문서](https://docs.kernel.org/)
- [ARM64 부팅](https://docs.kernel.org/arch/arm64/booting.html)
- [Kbuild](https://docs.kernel.org/kbuild/index.html)
- [드라이버 모델](https://docs.kernel.org/driver-api/driver-model/index.html)
- [메모리 관리](https://docs.kernel.org/mm/index.html)
- [cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [전원 관리](https://docs.kernel.org/power/index.html)

이 링크는 개념 안내다. 실제 구현은 해당 커널 소스의 Documentation과 대조한다. 최신 문서의 API를 4.19에 그대로 적용하지 않는다.
