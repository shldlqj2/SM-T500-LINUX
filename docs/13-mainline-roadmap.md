# 13. 메인라인 커널과 장기 유지

## 위치와 목표

제조사 커널의 정상 Debian 환경을 보존하면서 upstream Linux 기반 SM-T500 보드 지원을 개발한다. Debian 13 전환은 커널 이식과 구분해 검증한다. 높은 버전 번호나 부팅 로고만으로 메인라인 이식 완료를 선언하지 않는다.

upstream에는 SM6115 공통 DTSI가 있지만 이것이 SM-T500 전체 보드 지원을 뜻하지 않는다. 패널·터치 변형·전원 배선·펌웨어·reserved-memory 등 기기별 지원을 별도로 확인해야 한다.

## 시작 조건

- 마지막 정상 제조사 커널·모듈·DT·rootfs와 복구 기록이 있다.
- 기기 기준표와 실제 부품 목록이 있다.
- 화면 없이도 최소 하나의 관측 경로가 있거나 조기에 이를 만드는 계획이 있다.
- 기능별 driver/API/firmware 의존성 표가 있다.
- upstream 기준 tag·commit을 고정하고 지원 상태를 조사했다.

기준 커널 버전은 작업 시작 시 지원되는 upstream/LTS와 해당 SoC 지원을 비교해 선택하고 [결정 기록](decisions.md)에 남긴다. 현재 알지 못하는 미래 버전을 미리 하드코딩하지 않는다.

## 이식 순서

| 단계 | 대상 | 종료 조건 |
| --- | --- | --- |
| U0 비교 | upstream SoC·PMIC·보드 유사 사례와 vendor tree | 재사용·미지원 목록 |
| U1 초기 부팅 | CPU·메모리·reserved regions·timer·IRQ | 커널 진입 로그 |
| U2 공급자 | regulator·clock·pinctrl·bus | 필수 probe·의존성 충족 |
| U3 진단·rootfs | USB·SD·ext4·initramfs | 콘솔·Debian 셸 |
| U4 사용성 | panel·backlight·touch·buttons | GUI 입력 |
| U5 무선 | Wi-Fi·Bluetooth·firmware | 연결·재연결 |
| U6 전체 기능 | GPU·audio·camera·sensors·GNSS·PM | 기능별 검사 |
| U7 전환 | Debian 13·runtime·업데이트 | 전체 회귀·복구·장기 유지 명세 |

기능이 부족한 메인라인 이미지는 연구 세트로 둔다. 원래 기능표를 낮춰서 '완료'로 만들지 않는다. 실제 전환은 필요한 기능과 안정성을 확보한 후 수행한다.

## DT와 드라이버 원칙

vendor DTS 전체를 복사하지 않는다. 기존 upstream SoC/PMIC 공통 노드를 재사용하고 보드 배선·부품만 board DTS에서 표현한다. 공급자와 consumer 관계, voltage·reset·IRQ polarity·panel timing을 실제 자료로 확인한다.

reserved-memory는 firmware·secure world·remote processor 사용 영역을 조사해 옮긴다. 주소를 추정하거나 충돌을 무시하면 초기 부팅뿐 아니라 후속 DMA·DSP 동작에서 문제가 날 수 있다.

추가 binding은 schema와 예제를 제공하고 dt_binding_check/dtbs_check를 해당 tree에서 실행한다. schema 통과는 하드웨어 동작 증거가 아니며 둘 다 필요하다.

공통 드라이버가 부품을 지원하면 compatible·quirk 추가로 해결 가능한지 먼저 검토한다. vendor driver를 그대로 이식할 때는 API·전원 모델·userspace ABI 차이를 명시한다.

## 그래픽·HAL 전환

메인라인에서 표준 DRM/MSM·Mesa 경로가 동작하면 vendor KGSL/libhybris 경로와 분리해 검증한다. 이전 HAL이 특정 vendor ioctl·firmware 인터페이스에 묶여 있으면 메인라인에서 그대로 사용할 수 없을 수 있다.

HAL은 표준 경로로 대체한 기능부터 제거한다. 제거 전후 단독·통합 시험과 메모리·CPU·전원 비용을 비교한다. firmware 사용까지 곧바로 제거할 수 있다고 가정하지 않는다.

## Debian 13 전환

별도 rootfs 이미지로 생성하고 먼저 기본 부팅·systemd·udev·network·Docker를 시험한다. 커널 변경과 배포판 업그레이드를 동시에 해 원인 분리를 어렵게 만들지 않는다.

새 systemd·container runtime·Mesa·BlueZ의 실제 kernel/API 요구사항을 조사한다. 사용자 공간 요구를 낮추는 임시 우회와 기능 동등성 달성을 구분한다. rollback용 Debian 12 이미지를 보존한다.

## 패치와 유지관리

DT·driver·config·userspace 변경을 논리적으로 분리하고 각 패치에 문제, 실제 부품, 구현 이유, 시험 결과를 남긴다. 공개 제출은 사용자가 요청한 시점에 별도로 수행한다.

업데이트마다 기준 tag·패치 적용 결과·보안 변경·영향 기능을 기록한다. 커널 업데이트가 필요해도 자동으로 기기에 기록하지 않는다. 정상 세트와 실험 세트를 구분하고 [회귀 기준](11-validation-and-milestones.md)을 적용한다.

## 참고

- [upstream SM6115 DTSI](https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/qcom/sm6115.dtsi)
- [DT binding 작성](https://docs.kernel.org/devicetree/bindings/writing-schema.html)
- [커널 패치 제출 지침](https://docs.kernel.org/process/submitting-patches.html)
