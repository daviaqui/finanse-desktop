class ApiError(Exception):
    """An expected failure that is safe to expose to API clients."""

    def __init__(
        self,
        *,
        status_code: int,
        detail: str,
        code: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.code = code
        self.headers = headers


class ConflictError(ApiError):
    def __init__(self, *, detail: str, code: str) -> None:
        super().__init__(status_code=409, detail=detail, code=code)


class EmailAlreadyRegisteredError(ConflictError):
    def __init__(self) -> None:
        super().__init__(
            detail="Este e-mail já está cadastrado",
            code="email_already_registered",
        )


class CategoryNameConflictError(ConflictError):
    def __init__(self) -> None:
        super().__init__(
            detail="Você já possui uma categoria com esse nome",
            code="category_name_conflict",
        )
