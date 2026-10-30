# 삼성 펌웨어 Git 게시 검토 — 2026-10-30

## 결론과 게시 범위

사용자는 인수인계·현재 작업을 커밋하고, 삼성 펌웨어 게시에 문제가 있으면 해당 자료를 제외해 푸시하도록 요청했다. 검토 결과 **전체 순정 펌웨어의 재배포 권한을 확인하지 못했으므로 바이너리는 게시하지 않는다.** 로컬 원본은 보존하고 출처·파일 이름·크기·해시·분석 요약과 직접 작성한 포팅 문서/소스만 커밋한다.

이 결론은 모든 펌웨어·모든 관할에서의 위법성을 단정하는 법률 판정이 아니다. 확인한 이용 조건과 파일 내용/크기에 따른 이번 저장소의 게시 결정이다.

## 권리와 호스팅 정책 확인

삼성의 [공식 모바일 이용 조건](https://www.samsung.com/us/support/legal/LGL10000282/) 중 EULA §4는 제한적 사용과 백업 복제를 설명하고, §5는 명시적으로 부여하지 않은 권리의 유보, §6은 재허락과 권리 이전의 제한을 설명한다. 오픈소스 구성요소에는 해당 라이선스가 우선할 수 있다고 명시하지만, 전체 AP·BL·CSC 이미지의 공개 재배포 허락은 확인되지 않는다.

이 페이지는 미국 모바일 제품의 일반 약관이며 2024-02-05 갱신 표기다. 제공된 XAR 패키지에 실제 동봉/적용되는 개별 계약과 모든 파일의 라이선스를 전부 확정한 것은 아니다. 무료 다운로드 가능 여부나 제3자 사이트의 파일 제공만으로 우리 저장소의 재배포 권한이 생긴다고 판단하지 않는다. GPL 등으로 공개된 소스와 삼성/제3자의 독점 바이너리가 포함된 전체 패키지를 구분한다. 추후 특정 firmware 파일을 배포하려면 파일별 출처·명시적 라이선스·고지 및 배포 조건을 따로 검토한다.

[GitHub 파일 제한](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)에 따르면 일반 Git은 100MiB 초과 파일을 거부한다. 제공 AP와 CSC/HOME_CSC는 이를 넘는다. BL은 제한 이하이지만 크기로 재배포 권한이 입증되지는 않는다. LFS·Release로 옮겨도 저작권 검토를 대체하지 않는다. GitHub는 [DMCA 정책](https://docs.github.com/en/site-policy/content-removal-policies/dmca-takedown-policy)에 따라 권리 침해 주장에 대한 삭제 절차를 운영한다.

## 로컬 파일과 제외 대상

| 자료 | 확인한 크기/형태 | 처리 |
| --- | --- | --- |
| AP tar.md5 | 5,397,688,445 bytes | Git 제외, 로컬 보존 |
| BL tar.md5 | 36,761,710 bytes | Git 제외, 로컬 보존 |
| CSC tar.md5 | 181,483,622 bytes | Git 제외, 로컬 보존 |
| HOME_CSC tar.md5 | 181,463,147 bytes | Git 제외, 로컬 보존 |
| 동봉 안내 txt | 719 bytes | 원본 폴더와 함께 Git 제외 |
| 추출 boot/recovery/DT·config·vendor 자료·REA 원본 | `private/firmware/`, `private/nura/` 등 | 원문과 바이너리는 Git 제외 |
| N1/N2 이미지·APK·kernel·모듈·로그·서명 개인 키 | `artifacts/`, WSL 작업 공간, `private/` | 이번 푸시 대상에서 제외 |
| [패키지 조사 요약](T500XXS8CXG1.md)·본 검토 | 설명·메타데이터·해시·출처 링크 | 내용 검사 후 포함 |
| `ports/` | 직접 작성한 APKBUILD·deviceinfo·DTS·patch·도구 | 원래 SPDX/출처를 유지하고 포함. 순정 payload 없음 |

`.gitignore`의 원본 폴더·비공개 디렉터리 제외와 함께 SAMFW 폴더 패턴, tar.md5·img·bin·lz4·dtb·dtbo·apk·ko 등의 제외 규칙을 확인/보강했다. 이 규칙만으로 이미 추적된 파일이나 과거 commit의 blob이 제외되는 것은 아니므로 현재 index와 도달 가능한 Git 이력도 따로 검사한다.

## 게시 전 검사와 인수인계

실행 환경은 Windows PowerShell/Python, cwd는 저장소 루트다. 커밋 후보의 파일 형식·크기·바이너리 여부·비밀값/식별자 패턴, 추적 파일/이력의 금지 경로·대용량 blob, staged 파일의 실제 내용을 검사한다. 상대 링크·문자/fence/공백과 `git diff --check`도 확인한다. 명령·결과는 Git 제외 경로 `private/publication/20261030/`에 보존한다.

정확한 게시 상태·마지막 확인과 다음 작업은 [HANDOFF](../../HANDOFF.md)를 따른다. 이번 게시에는 펌웨어 원본이나 전체 덤프가 포함되지 않으므로 새 checkout에서 이를 자동으로 얻을 수 없다. 원본·비공개 산출물은 HANDOFF의 동일 PC/WSL 경로에서 별도 접근해야 한다. 다른 에이전트 실행·기기 변경은 이 요청 범위에 포함하지 않는다.
