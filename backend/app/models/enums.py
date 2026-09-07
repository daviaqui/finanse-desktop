from enum import Enum


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionStatus(str, Enum):
    PAID = "paid"
    PENDING = "pending"
