# SM-T500 Nura 기기 패키지 — N2 오프라인 준비

현재 0.2-r0은 Nura 26.06 aarch64와 공식 `linux-postmarketos-lts=6.18.35-r0`, 시험용 `dtb-samsung-gta4lwifi=0.1-r0`을 연결한다. `modules-initfs`로 QUSB2 PHY를 초기 archive에 포함한다. `flash_method=none`, `generate_bootimg=false`이며 기기에 기록할 boot 이미지를 제공하지 않는다.

2026-10-30 [N2 실행](../../docs/research/nura-n2-dt-2026-10-30.md)에서 DT·기기 APK 빌드·source SHA-512 검사와 `pmbootstrap install --no-image`가 종료 0으로 완료됐다. kernel/config·DTB·initramfs·모듈·383개 패키지의 대응을 검사했다. kernel은 공식 APK에서 설치했으며 로컬 kernel 전체 빌드는 수행하지 않았다.

[N1 기록](../../docs/research/nura-n1-rootfs-2026-10-30.md)의 0.1-r0은 kernel 없는 metadata-only 초안이다. 당시 mkinitfs 실패는 N2에서 해소됐으나 N1 ext4 이미지에는 N2 모듈이 없으므로 두 세트를 결합하지 않는다.

기존 Tab A7 기기 패키지를 복사하지 않고 사용자 확인 모델·코드명과 공식 deviceinfo 규격에서 최소 항목을 작성했다. 모델·아키텍처·연도는 순정 자료/공개 기기 정의와 대조한 정적 정보이며 실기기 조사 완료를 뜻하지 않는다. SD 보유는 사용자 설명이고 SD 부팅은 미검증이다.

실제 부품·DT 선택·메모리 예약·boot header/offset·SD UUID/실패 정책·USB 열거는 미검증이다. firmware도 도입하지 않았다. N2 rootfs는 WSL 패키지 트리이며 별도 ext4 파일은 없다. 현재 상태는 N2 부분 완료이며 기기 부팅·하드웨어 지원 성공이 아니다. 전체 범위는 [포팅 계획](../../docs/14-nura-26.06-port-plan.md)을 따른다.
