"""Fixed commands only; discovered names are checked and quoted on device."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Probe:
    id: str
    command: str
    parser: str = "scalar"
    required: bool = False
    binary: bool = False
    purpose: str = ""
    meaning: str = "등록된 인터페이스 관측이며 하드웨어 실동작은 별도 확인이 필요합니다."


BY_NAME = """for d in /dev/block/by-name /dev/block/bootdevice/by-name; do
printf 'DIR\\t%s\\n' "$d"
if [ ! -e "$d" ]; then printf 'MISSING\\n'
elif [ ! -r "$d" ]; then printf 'DENIED\\n'
else ls -l "$d" || printf 'FAILED\\n'; fi
done"""
CONFIG = """p=/proc/config.gz
if [ ! -e "$p" ]; then printf 'PORTCTL-ERROR path_unavailable\\n'
elif [ ! -r "$p" ]; then printf 'PORTCTL-ERROR permission_denied\\n'
else cat "$p"; fi"""
DT = """printf 'PORTCTL-DT1\\n'
for k in model compatible '#address-cells' '#size-cells'; do
p="/sys/firmware/devicetree/base/$k"
if [ ! -e "$p" ]; then printf '%s missing 0\\n\\n' "$k"
elif [ ! -r "$p" ]; then printf '%s denied 0\\n\\n' "$k"
else n=$(wc -c < "$p") || exit 1
printf '%s ok %s\\n' "$k" "$n"
cat "$p" || exit 1
printf '\\n'; fi
done"""

HEADER = "printf 'PORTCTL-SYS1\\n'\n"
READ_ATTR = """read_attr() {
if [ ! -e "$1" ]; then printf '!missing'
elif [ ! -r "$1" ]; then printf '!denied'
else cat "$1" || printf '!failed'; fi
}
"""
CHECK_NAME = """n=${p##*/}
case "$n" in ''|*[!a-zA-Z0-9_.:+-]*) printf 'FAILED\\tname\\n'; exit 1;; esac
c=$((c+1)); if [ "$c" -gt 128 ]; then printf 'LIMIT\\t%s\\n' "$d"; break; fi
"""


def class_attributes(directories, attributes):
    return HEADER + READ_ATTR + f"for d in {directories}; do\n" + """c=0
if [ ! -d "$d" ]; then printf 'MISSING\\t%s\\n' "$d"; continue; fi
if [ ! -r "$d" ]; then printf 'DENIED\\t%s\\n' "$d"; continue; fi
for p in "$d"/*; do
[ -e "$p" ] || continue
""" + CHECK_NAME + f"for a in {attributes}; do\n" + """v=$(read_attr "$p/$a")
printf 'ATTR\\t%s\\t%s\\t%s\\t%s\\n' "${d##*/}" "$n" "$a" "$v"
done
done
done"""


DRIVERS = HEADER + """for d in /sys/class/input /sys/class/drm /sys/class/graphics /sys/class/backlight /sys/class/net; do
c=0
if [ ! -d "$d" ]; then printf 'MISSING\\t%s\\n' "$d"; continue; fi
if [ ! -r "$d" ]; then printf 'DENIED\\t%s\\n' "$d"; continue; fi
for p in "$d"/*; do
[ -e "$p" ] || continue
""" + CHECK_NAME + """for a in driver of_node; do
v='!missing'
if [ -e "$p/device/$a" ]; then v=$(readlink -f "$p/device/$a") || v='!failed'
elif [ -e "$p/$a" ]; then v=$(readlink -f "$p/$a") || v='!failed'; fi
printf 'ATTR\\t%s\\t%s\\t%s\\t%s\\n' "${d##*/}" "$n" "$a" "$v"
done
done
done"""
POWER = class_attributes("/sys/class/power_supply", "type status capacity voltage_now current_now temp")
THERMAL = class_attributes("/sys/class/thermal", "type temp").replace('for p in "$d"/*;', 'for p in "$d"/thermal_zone*;')
RESOLVED = HEADER + """for d in /dev/block/by-name /dev/block/bootdevice/by-name; do
c=0
if [ ! -d "$d" ]; then printf 'MISSING\\t%s\\n' "$d"; continue; fi
if [ ! -r "$d" ]; then printf 'DENIED\\t%s\\n' "$d"; continue; fi
for p in "$d"/*; do
[ -L "$p" ] || continue
""" + CHECK_NAME + """r=$(readlink -f "$p") || { printf 'FAILED\\t%s\\n' "$p"; continue; }
case "$r" in /dev/block/*) ;; *) printf 'FAILED\\t%s\\n' "$p"; continue;; esac
k=${r##*/}
case "$k" in ''|*[!a-zA-Z0-9_.+-]*) printf 'FAILED\\t%s\\n' "$p"; continue;; esac
if [ ! -e "/sys/class/block/$k/dev" ] || [ ! -e "/sys/class/block/$k/size" ]; then printf 'MISSING\\t%s\\n' "$p"; continue; fi
if [ ! -r "/sys/class/block/$k/dev" ] || [ ! -r "/sys/class/block/$k/size" ]; then printf 'DENIED\\t%s\\n' "$p"; continue; fi
dev=$(cat "/sys/class/block/$k/dev") || { printf 'FAILED\\t%s\\n' "$p"; continue; }
sz=$(cat "/sys/class/block/$k/size") || { printf 'FAILED\\t%s\\n' "$p"; continue; }
printf 'PART\\t%s\\t%s\\t%s\\t%s\\t%s\\n' "$d" "$n" "$r" "$dev" "$sz"
done
done"""


def prop(id, name, purpose, required=False):
    return Probe(id, f"getprop {name}", required=required, purpose=purpose,
                 meaning="ROM이 보고한 속성입니다. 실제 부트로더·펌웨어 동작과 대조해야 합니다.")


BASIC = (
    prop("identity.model", "ro.product.model", "SM-T500 대상 식별", True),
    prop("identity.codename", "ro.product.device", "gta4lwifi 코드명 식별", True),
    prop("identity.rom_build", "ro.build.fingerprint", "ROM 소스 대응 근거"),
    prop("identity.vendor_build", "ro.vendor.build.fingerprint", "vendor/HAL 대응 근거"),
    prop("identity.bootloader", "ro.bootloader", "부트로더 리비전 기록"),
    prop("boot.verified_state", "ro.boot.verifiedbootstate", "verified boot 보고 속성"),
    prop("boot.vbmeta_state", "ro.boot.vbmeta.device_state", "vbmeta 보고 속성"),
    Probe("kernel.release", "uname -r", required=True, purpose="실행 중인 커널 release", meaning="모듈·소스 대응을 확인할 기준입니다."),
    Probe("kernel.version", "cat /proc/version", purpose="커널 빌드 문자열"),
    Probe("boot.cmdline", "cat /proc/cmdline", purpose="부트로더가 전달한 인수"),
    Probe("memory.info", "cat /proc/meminfo", "memory", purpose="실제 RAM 및 현재 가용 메모리"),
    Probe("storage.partitions", "cat /proc/partitions", "partitions", purpose="파티션 이름과 용량"),
    Probe("storage.mounts", "cat /proc/mounts", "mounts", purpose="현재 마운트 목록"),
    Probe("storage.by_name", BY_NAME, "by_name", purpose="두 by-name 인터페이스 대조"),
    Probe("kernel.modules", "cat /proc/modules", "modules", purpose="현재 적재 모듈", meaning="빈 목록도 정상 관측입니다. built-in 드라이버는 이 목록에 없습니다."),
    Probe("input.devices", "cat /proc/bus/input/devices", "inputs", purpose="입력 장치와 handler 목록", meaning="실제 터치 입력은 수동으로 확인해야 합니다."),
)
EXTENDED = (
    Probe("kernel.config", CONFIG, "config", binary=True, purpose="실행 커널 Kconfig", meaning="gzip CRC와 설정을 확인합니다. 소스 기본 설정과 다를 수 있습니다."),
    Probe("dt.identity", DT, "dt", binary=True, purpose="실행 DT 식별과 cell 폭", meaning="NUL 문자열과 big-endian cell을 해석합니다."),
    Probe("storage.resolved", RESOLVED, "sysfs", purpose="파티션 실제 대상과 sysfs 용량", meaning="512-byte sector 규칙으로 환산합니다. block 내용은 읽지 않습니다."),
    Probe("drivers.bindings", DRIVERS, "sysfs", purpose="class의 driver·of_node 연결"),
    Probe("power.supplies", POWER, "sysfs", purpose="전원 공급 장치 속성", meaning="단위가 미확정인 값은 원시 정수로 보존합니다."),
    Probe("thermal.zones", THERMAL, "sysfs", purpose="thermal zone 종류와 온도 값"),
    Probe("kernel.log", "dmesg", purpose="한 번의 커널 로그 snapshot", meaning="특정 드라이버 원인을 자동 확정하지 않습니다."),
)
DIAGNOSTICS = {
    "host.adb_version": Probe("host.adb_version", "", "version", True, purpose="ADB 실행 및 버전 확인"),
    "transport.devices": Probe("transport.devices", "", required=True, purpose="ADB 대상 목록"),
    "transport.shell_ok": Probe("transport.shell_ok", "exit 0", required=True, purpose="원격 성공 종료 전달"),
    "transport.shell_fail": Probe("transport.shell_fail", "exit 37", required=True, purpose="원격 실패 종료 전달"),
    "privilege.root": Probe("privilege.root", "su -c 'id -u'", "uid", purpose="기존 su UID 0 확인"),
}
ALL = {probe.id: probe for probe in BASIC + EXTENDED}
ALL.update(DIAGNOSTICS)
