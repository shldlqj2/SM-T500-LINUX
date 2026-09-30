ERRORS = {
    "tool_missing": "필요한 실행 파일을 찾지 못했습니다.",
    "tool_failed": "실행 파일을 정상적으로 실행하지 못했습니다.",
    "unsupported_platform": "지원하지 않는 실행 환경입니다.",
    "invalid_arguments": "명령 인수를 확인하세요.",
    "invalid_schema": "지원하는 데이터 계약과 일치하지 않습니다.",
    "no_device": "선택할 기기가 없습니다.",
    "multiple_devices": "여러 기기가 있어 명시적 선택이 필요합니다.",
    "unauthorized": "기기에서 USB 디버깅 인증을 확인하세요.",
    "offline": "ADB 기기가 offline 상태입니다.",
    "unsupported_device_state": "일반 Android device 상태가 아닙니다.",
    "model_mismatch": "SM-T500/gta4lwifi 식별 값과 일치하지 않습니다.",
    "identity_unverified": "필수 기기 식별 값을 확보하지 못했습니다.",
    "protocol_unsupported": "원격 종료 상태 전달을 확인하지 못했습니다.",
    "device_disconnected": "선택한 기기 연결이 끊겼습니다.",
    "path_unavailable": "요청한 읽기 인터페이스를 확인하지 못했습니다.",
    "permission_denied": "읽기 권한이 부족합니다.",
    "root_unavailable": "기존 su의 UID 0 권한을 확인하지 못했습니다.",
    "timeout": "수집 시간 제한을 넘겼습니다.",
    "output_limit": "항목 출력 제한을 넘겼습니다.",
    "output_budget": "실행 전체의 원본 용량 한도에 도달했습니다.",
    "parse_error": "원본 형식을 정상적으로 해석하지 못했습니다.",
    "command_failed": "읽기 명령이 실패했습니다.",
    "user_interrupted": "사용자가 실행을 중단했습니다.",
    "cleanup_unconfirmed": "종료된 ADB 클라이언트의 원격 작업 종료는 미확인입니다.",
    "incomplete_run": "최종 JSON이 없는 미종결 실행입니다.",
    "draft_input": "확정되지 않은 입력입니다.",
    "lock_busy": "workspace의 다른 수집 또는 잔존 잠금을 확인하세요.",
    "input_mismatch": "입력 파일 해시가 일치하지 않습니다.",
    "source_dirty": "준비된 소스에 예상 밖 변경이 있습니다.",
    "unsafe_path": "허용한 파일 경로 밖으로 접근할 수 없습니다.",
    "unsupported_archive": "지원하지 않는 archive입니다.",
    "download_failed": "다운로드가 실패했습니다.",
    "config_mismatch": "최종 커널 설정이 요구와 다릅니다.",
    "artifact_missing": "필요한 파일이 없습니다.",
    "artifact_mismatch": "기록된 파일의 크기 또는 해시가 다릅니다.",
    "unexpected_artifact": "예상하지 않은 파일이 있습니다.",
    "internal_error": "도구 내부 오류가 발생했습니다.",
}
PROBE_STATUSES = {"ok", "unavailable", "permission_denied", "timeout",
                  "truncated", "parse_error", "failed", "skipped"}
RUN_STATUSES = {"complete", "partial", "failed", "interrupted"}


class PortError(Exception):
    def __init__(self, code, exit_code=3):
        super().__init__(ERRORS[code])
        self.code = code
        self.exit_code = exit_code
