# 09. Debian 사용자 공간·터치 데스크톱·Docker

## 선행 조건과 기본값

Debian 12 bookworm arm64 minimal, systemd, SSH, NetworkManager, Xfce/X11, Onboard를 기준으로 한다. [부팅 설계](05-boot-and-image-design.md)에 따라 microSD rootfs로 직접 전환한다. 초기에는 내부 userdata나 Android의 /data 파일시스템을 변경하지 않는다.

## rootfs 생성

1. debootstrap으로 bookworm/arm64 최소 rootfs 생성.
2. x86-64 호스트에서 foreign second stage가 필요하면 검증한 QEMU userspace 경로 사용.
3. apt keyring·저장소 서명 검증을 유지하고 사용한 패키지 버전 목록 저장.
4. systemd-sysv·udev·DBus·기본 네트워크·SSH 등 최소 부팅 패키지 추가.
5. 대응 /lib/modules, firmware, fstab, hostname, 사용자 계정, SSH 키 구성.
6. 4.19 호환 ext4 feature로 이미지 생성하고 UUID와 marker 기록.
7. rootfs 내용·권한·동적 loader·/sbin/init 링크 검사.
8. QEMU에서 가능한 사용자 공간 시험 후 실제 커널에서 재검증.

QEMU virt 시험용 rootfs는 virt 전용 모듈과 기기용 모듈이 혼동되지 않게 별도 식별한다. mmc 장치 순서를 고정하지 않고 UUID로 마운트한다. 부팅에 필요하지 않은 SD 교환 파티션은 v1에서 만들지 않는다.

포트 전용 커널의 설치·업데이트 경로를 문서화하고 일반 Debian 커널 패키지가 현재 boot 이미지를 자동 대체한다고 가정하지 않는다. apt 업데이트와 태블릿 커널 업데이트는 별도 작업이다.

## 최소 서비스

처음에는 multi-user.target로 부팅한다. host PID 1·udev·DBus·journal·SSH·시간 동기화·네트워크를 확인한 뒤 GUI를 추가한다.

~~~sh
ps -p 1 -o pid,comm,args
uname -a
findmnt /
systemctl --failed
journalctl -b -p warning
cat /proc/cgroups
findmnt /sys/fs/cgroup
~~~

위 명령은 미래의 검증 예시다. 실패 unit이 있다면 장치에 해당하지 않는 서비스인지 필수 서비스 실패인지 원인을 분류한다. 단순히 mask해서 실패 목록을 비우지 않는다.

SSH는 키 인증을 기본으로 하고 비밀번호·기본 계정 정보를 공개 저장소에 넣지 않는다. 초기 로그는 용량 제한을 두고 필요한 증거는 PC로 회수한다. NTP 이전 시간과 이후 시간을 구분해 로그를 해석한다.

## Xfce와 터치

GPU 가속 전에는 compositor를 끄고 장식·상주 서비스를 최소화한다. 그래픽 초기화 경로는 [하드웨어 문서](07-hardware-enablement.md)를 따른다.

초기 GUI는 Xorg + Xfce, 로그인 관리자는 LightDM을 기준으로 한다. LightDM greeter에서 접근성 키보드 호출이 되는지 별도 시험하고 지원이 부족하면 로그인 가능한 대체 greeter 설정을 검증한다. 자동 로그인으로 입력 문제를 숨기지 않는다.

Onboard는 패널에서 항상 터치로 호출할 수 있게 한다. 앱 포커스에 따른 자동 표시가 가능하면 추가하지만 수동 호출 경로도 유지한다. 작은 UI에는 DPI·폰트·패널 크기를 조정하고 실제 패널에서 확인한다.

터치는 evdev/libinput → Xorg 경로로 연결한다. 회전은 xrandr 출력 변환과 input 좌표 변환을 함께 적용한다. 센서가 아직 없으면 수동 회전 버튼부터 구현하고 센서 지원 후 자동 회전으로 확장한다.

합격 작업은 터치만으로 로그인 → 터미널 실행 → 키보드 입력 → 창 전환 → 네트워크 설정 → 로그아웃이다. 멀티터치 장치 지원과 앱별 pinch gesture는 별도 기능으로 추적한다.

## Docker Engine

초기 패키지는 Debian bookworm의 docker.io·containerd·runc 조합으로 검증한다. 외부 저장소의 최신 Docker로 자동 교체하지 않는다. 실제 설치 시 지원·보안 상태와 arm64 패키지를 확인하고 기록한다.

일반 rootful Engine으로 시작한다. 시험 컨테이너는 privileged 모드를 사용하지 않고 필요 없는 host device·host network를 전달하지 않는다. Docker 그룹은 강한 호스트 권한을 가지므로 사용자 편의를 위해 자동 추가하지 않는다.

커널 요구를 순서대로 검사한다.

1. namespace 기능과 기본 컨테이너 실행.
2. cgroup CPU·memory·PID 제어와 runtime 연동.
3. seccomp 적용과 기본 profile 호환성.
4. OverlayFS 저장소와 실제 backing ext4 기능.
5. veth·bridge·netfilter·NAT·DNS·포트 공개.
6. 영속 볼륨·정상 종료·재부팅 후 재시작.

docker info의 kernel·cgroup driver/version·storage driver를 기록한다. v2를 우선하고 기능이 부족하면 별도 v1 부팅 프로필로 시험한다. v1/v2를 서비스 실행 중 섞어 전환하지 않는다.

iptables/nft 사용 여부는 설치 패키지와 커널 기능을 대조해 정한다. 네트워크 문제가 생기면 namespace → veth → bridge → forwarding → netfilter → uplink 순서로 조사한다. 원인 없이 방화벽을 전부 비활성화하지 않는다.

## 기준 부하

| 작업 | 초기 제한 | 데이터·네트워크 |
| --- | --- | --- |
| ARM64 웹 서버 | 128MiB, pids 128, CPU 1개 분량 | 시험 페이지, 명시적 공개 포트 |
| 소형 API | 256MiB, pids 128, CPU 1개 분량 | 작은 영속 데이터, 내부 서비스 연결 |

이미지는 실제 선택 시 태그와 digest를 함께 고정한다. 컨테이너의 단순 hello-world 성공만으로 전체 완료를 선언하지 않는다. 요구 메모리가 제한을 넘는 경우 시험 앱을 작게 만들고 실제 대형 앱 요구와 혼동하지 않는다.

메모리 시험·zram·서버 실행 중 절전 정책은 [10 문서](10-memory-power-and-stability.md)를 따른다. 멀티 아키텍처 이미지가 없을 때 x86 에뮬레이션으로 ARM64 네이티브 성공을 주장하지 않는다.

## 완료 산출물

rootfs recipe·패키지 명세, systemd units, GUI 설정, 터치 조작 시험, Docker daemon 설정·이미지 digest·시험 결과, 부팅 후 서비스 회복 기록을 보존한다. 구체적인 시험 횟수는 [검증 기준](11-validation-and-milestones.md)에 따른다.

## 참고

- [Debian bookworm](https://www.debian.org/releases/bookworm/index)
- [Debian docker.io 패키지](https://packages.debian.org/bookworm/docker.io)
- [Docker daemon 진단](https://docs.docker.com/engine/daemon/troubleshoot/)
- [Xfce 접근성](https://docs.xfce.org/xfce/xfce4-settings/accessibility)
