# SM-T500 Wi-Fi 시험용 DT

Linux 6.18.35의 SM6115 공통 DTSI와 제공 순정 `T500XXS8CXG1`의 Bengal 후보를 대조해 SD·USB 초기 진단용 DT를 작성했다. **정적 컴파일·패키징용 초안이며 기기에 기록할 수 있는 부팅 세트가 아니다.** 실제 기기가 선택한 base DT/DTBO·메모리 예약·bootloader의 DT 선택 방식은 미확인이다.

SM-T500/gta4lwifi 전용이다. `remoteproc_mpss`·IPA·셀룰러 서비스는 활성화하지 않는다. 공통 SoC DTSI의 비활성 노드·메모리 예약은 삭제하지 않았으며 이 존재를 LTE 지원으로 해석하지 않는다. Wi-Fi의 공유 무선 서브시스템 의존성은 후속 분석 대상이다.

## 파일과 재현

- `sm6115-samsung-gta4lwifi.dts`: SD L22/L5·카드 감지 GPIO 88·USB L4/L12/L15 연결. L7 bias의 always-on 처리는 시험 가설이며 실기기 검증 전이다.
- `APKBUILD`: 공식 recipe와 같은 SHA-512로 Linux 6.18 및 6.18.35 stable patch를 검증하고 DT만 컴파일하는 `noarch` 패키지. 커널 코드를 컴파일하지 않는다.
- `linux-integration.patch`: 같은 커널 소스의 Kbuild 목록과 `arm/qcom.yaml`에 새 보드 식별자를 추가하는 로컬 패치. APK 빌드에는 필요하지 않고 binding 검사·향후 커널 소스 통합에 사용한다.
- `build_dt.py`: 호스트 `gcc`·`dtc`로 보드 DT와 upstream Lenovo 비교 DT를 각각 빌드하고 include 입력·산출물 해시·명령·로그를 남긴다. 출력 디렉터리는 새 경로여야 한다.

Linux 환경에서 버전과 입력 해시를 확인한 뒤 실행한다. 아래 경로는 실제 Linux 6.18.35 소스와 새 출력 경로로 바꾼다.

~~~sh
python3 ports/dtb-samsung-gta4lwifi/build_dt.py \
  --linux /path/to/linux-6.18.35 --output /path/to/new-dt-output
~~~

`dtc` 성공과 binding 검사는 별개다. binding 검사 전 `linux-integration.patch`를 적용하고, [Linux DT schema 검사 지침](https://docs.kernel.org/devicetree/bindings/writing-schema.html)에 따라 `dt-validate`의 진단을 확인한다. 도구 종료 0만으로 검사 통과를 판정하지 않는다. 현재 전체 검사에는 비교 DT와 동일한 upstream GPU 진단 2개가 남아 있다.

## 출처·라이선스·제한

새 DTS의 라이선스는 `GPL-2.0-or-later OR BSD-3-Clause`다. SM6115·PM6125 공통 정의는 Linux 6.18.35의 원본 SPDX와 저작권을 유지한다. upstream 보드 DTS는 binding 표현의 참고·검사 대조군이며 다른 모델의 DTB·framebuffer·GPIO 45 우회 설정을 SM-T500 산출물에 넣지 않았다. 기존 Tab A7의 대량 `__symbols__`·LTE 이름·ramdisk offset도 도입하지 않았다. `-@`로 자동 생성하는 새 DT의 symbols와 원본의 수동 symbols 복제를 구분한다.

순정 DTB/DTBO 원문·firmware는 패키지 source에 포함하지 않는다. 추출된 연결 정보와 해시·접근 방법은 [N2 조사·실행 기록](../../docs/research/nura-n2-dt-2026-10-30.md)에 정리한다. boot 이미지 생성·기기 기록 전에는 [복구 관문](../../docs/03-backup-and-recovery.md)과 [이미지 계약](../../docs/05-boot-and-image-design.md)을 별도로 충족해야 한다.
