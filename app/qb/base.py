"""What the app needs from QuickBooks. The fake and the real Desktop connector both implement this."""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class QBJob:
    list_id: str  # QB's permanent ID for the Customer:Job
    full_name: str  # e.g. "Hillside Church:24-117 Fellowship Hall"
    customer: str


@dataclass
class QBCost:
    txn_date: str
    txn_type: str  # Bill, Check, Paycheck, CreditCardCharge, ...
    ref: str
    name: str  # vendor / employee
    account: str  # expense or COGS account the line hit
    memo: str
    amount: float


class Connector(Protocol):
    def find_jobs(self, search: str) -> list[QBJob]: ...

    def get_job(self, list_id: str) -> QBJob | None: ...

    def job_costs(self, list_id: str) -> list[QBCost]: ...

    def job_invoiced(self, list_id: str) -> float: ...
