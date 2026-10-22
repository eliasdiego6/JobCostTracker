"""Sample QuickBooks data so the app can be built and demoed on any PC without QuickBooks.

Costs are generated deterministically from each job's "plan" (budget, progress, overrun),
so the dashboard shows a realistic mix of on-track, trending and over-budget jobs.
"""

import random
from datetime import date, timedelta

from app.qb.base import QBCost, QBJob

# Accounts as they might appear in a QB chart of accounts, and the bucket each one feeds.
DEFAULT_ACCOUNT_MAP = {
    "5000 · Direct Labor": "labor",
    "5010 · Payroll Taxes - Field": "labor",
    "5100 · Job Materials": "material",
    "5200 · Subcontractors": "sub",
}

BUCKET_ACCOUNTS = {
    "labor": [("5000 · Direct Labor", 0.85), ("5010 · Payroll Taxes - Field", 0.15)],
    "material": [("5100 · Job Materials", 1.0)],
    "sub": [("5200 · Subcontractors", 1.0)],
    "misc": [
        ("5300 · Equipment Rental", 0.5),
        ("5400 · Permits & Fees", 0.3),
        ("5500 · Dump & Disposal", 0.2),
    ],
}

BUCKET_NAMES = {
    "labor": ["Field Payroll"],
    "material": ["ABC Supply", "Home Depot Pro", "Ferguson", "84 Lumber"],
    "sub": ["Rivera Electric", "Summit Plumbing", "Peak Drywall", "Delta HVAC"],
    "misc": ["Sunbelt Rentals", "City Permits Office", "Waste Management"],
}

TXN_TYPES = {"labor": "Paycheck", "material": "Bill", "sub": "Bill", "misc": "Check"}

# number, job name, customer, estimates (labor, material, sub, misc), contract,
# progress (0-1), overrun factor per bucket (1.0 = on budget at completion)
FAKE_JOBS = [
    ("24-101", "Fellowship Hall Remodel", "Hillside Church", (48000, 62000, 35000, 6000), 185000, 0.95, (1.02, 0.97, 1.0, 1.1)),
    ("24-108", "Office Tenant Improvement", "Harbor Point LLC", (32000, 41000, 22000, 4000), 118000, 0.60, (1.25, 1.05, 0.9, 1.0)),
    ("24-112", "Kitchen & Bath Addition", "Johnson Residence", (18000, 27000, 9000, 2500), 72000, 0.45, (0.95, 1.3, 1.0, 0.8)),
    ("24-117", "Warehouse Mezzanine", "Valley Logistics", (26000, 58000, 14000, 5000), 128000, 0.80, (1.0, 1.0, 1.4, 1.2)),
    ("24-121", "Clinic Exam Room Refresh", "Northside Medical", (15000, 19000, 12000, 1500), 61000, 0.25, (0.9, 0.85, 1.0, 1.0)),
    ("24-125", "Retail Storefront Buildout", "Main Street Coffee", (21000, 24000, 18000, 3000), 82000, 1.00, (1.08, 1.12, 1.05, 1.3)),
    ("24-130", "Roof Replacement", "Oak Ridge HOA", (22000, 46000, 0, 3500), 88000, 0.70, (1.0, 0.98, 1.0, 1.0)),
    ("24-134", "Classroom Wing Renovation", "Lincoln Elementary", (64000, 71000, 52000, 9000), 236000, 0.35, (1.3, 1.1, 1.05, 1.0)),
    ("24-139", "Deck & Patio", "Garcia Residence", (9000, 14000, 0, 800), 31000, 0.90, (0.92, 0.95, 1.0, 1.0)),
    ("24-142", "Server Room Upgrade", "Harbor Point LLC", (12000, 9000, 26000, 1200), 58000, 0.15, (1.0, 1.0, 1.0, 1.0)),
    ("24-146", "Basement Finish", "Patel Residence", (14000, 16000, 11000, 1500), 52000, 0.05, (1.0, 1.0, 1.0, 1.0)),
    ("24-150", "Parking Lot Lighting", "Valley Logistics", (6000, 18000, 21000, 2000), 55000, 0.0, (1.0, 1.0, 1.0, 1.0)),
]


def _job(row) -> QBJob:
    number, name, customer, *_ = row
    return QBJob(list_id=f"80000{number.replace('-', '')}-FAKE", full_name=f"{customer}:{number} {name}", customer=customer)


def _split(rng: random.Random, total: float, parts: int) -> list[float]:
    weights = [rng.uniform(0.5, 1.5) for _ in range(parts)]
    scale = total / sum(weights)
    amounts = [round(w * scale, 2) for w in weights]
    amounts[-1] = round(total - sum(amounts[:-1]), 2)
    return amounts


class FakeConnector:
    def __init__(self):
        self._rows = {_job(r).list_id: r for r in FAKE_JOBS}

    def find_jobs(self, search: str) -> list[QBJob]:
        s = search.strip().lower()
        return [_job(r) for r in FAKE_JOBS if s and s in _job(r).full_name.lower()]

    def get_job(self, list_id: str) -> QBJob | None:
        row = self._rows.get(list_id)
        return _job(row) if row else None

    def job_costs(self, list_id: str) -> list[QBCost]:
        row = self._rows.get(list_id)
        if not row:
            return []
        number, _, _, ests, _, progress, overrun = row
        rng = random.Random(number)
        start = date(2026, 3, 1) + timedelta(days=rng.randint(0, 120))
        costs = []
        for bucket, est, factor in zip(("labor", "material", "sub", "misc"), ests, overrun):
            target = est * progress * factor
            if target <= 0:
                continue
            for account, share in BUCKET_ACCOUNTS[bucket]:
                n = max(1, int(6 * progress * share) + 1)
                for i, amount in enumerate(_split(rng, target * share, n)):
                    costs.append(
                        QBCost(
                            txn_date=(start + timedelta(days=rng.randint(0, 90))).isoformat(),
                            txn_type=TXN_TYPES[bucket],
                            ref=str(rng.randint(1000, 9999)),
                            name=rng.choice(BUCKET_NAMES[bucket]),
                            account=account,
                            memo=f"{number} {bucket}",
                            amount=amount,
                        )
                    )
        return sorted(costs, key=lambda c: c.txn_date)

    def job_invoiced(self, list_id: str) -> float:
        row = self._rows.get(list_id)
        if not row:
            return 0.0
        number, _, _, _, contract, progress, _ = row
        rng = random.Random(number + "inv")
        return round(contract * progress * rng.uniform(0.7, 1.0), 2)
