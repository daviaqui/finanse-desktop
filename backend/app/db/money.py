from decimal import Decimal

from sqlalchemy import BigInteger
from sqlalchemy.types import TypeDecorator


class Money(TypeDecorator):
    """Decimal API, integer cents on disk: never pass currency through SQLite REAL."""

    impl = BigInteger
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        amount = Decimal(str(value))
        cents = amount * 100
        if not amount.is_finite() or cents != cents.to_integral_value():
            raise ValueError("O valor deve ter no máximo duas casas decimais")
        if not 0 < cents <= 99999999999999:
            raise ValueError("Valor fora do limite permitido")
        return int(cents)

    def process_result_value(self, value, dialect):
        return None if value is None else (Decimal(value) / 100).quantize(Decimal("0.01"))
