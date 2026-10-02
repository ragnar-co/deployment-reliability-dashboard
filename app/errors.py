INVALID_FILE = "INVALID_FILE"
VALIDATION_FAILED = "VALIDATION_FAILED"
DUPLICATE_FILE = "DUPLICATE_FILE"
DUPLICATE_DEPLOYMENT = "DUPLICATE_DEPLOYMENT"
FILE_TOO_LARGE = "FILE_TOO_LARGE"
INVALID_PARAMETER = "INVALID_PARAMETER"
IMPORT_BUSY = "IMPORT_BUSY"

HTTP_STATUS = {
    INVALID_FILE: 422,
    VALIDATION_FAILED: 422,
    DUPLICATE_FILE: 409,
    DUPLICATE_DEPLOYMENT: 409,
    FILE_TOO_LARGE: 413,
    INVALID_PARAMETER: 422,
    IMPORT_BUSY: 503,
}


class AppError(Exception):
    def __init__(self, code: str, errors: list[str]):
        super().__init__("; ".join(errors))
        self.code = code
        self.errors = errors

    @property
    def status_code(self) -> int:
        return HTTP_STATUS[self.code]
