"""Step 1 discovery: look at how YOUR QuickBooks data is set up. Read-only - changes nothing in QB.

Run on the server (or any PC with QuickBooks Desktop and the company file open):

    python -m scripts.qb_discover                  # QB version, list of jobs, accounts, items
    python -m scripts.qb_discover 24-117           # ...plus every cost posted to jobs matching "24-117"

Everything is written to discovery_output/ (not committed to git - it's company data).
summary.txt is the short version to review and share.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

from app.qb import qbxml
from app.qb.qbxml import QBError, Session, to_float

OUT = Path("discovery_output")


def write_csv(name: str, rows: list[dict]) -> Path:
    path = OUT / name
    cols = list(dict.fromkeys(k for r in rows for k in r))  # union of keys, first-seen order
    with path.open("w", newline="", encoding="utf-8-sig") as f:  # -sig so Excel opens it cleanly
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return path


class Summary:
    def __init__(self):
        self.lines = []

    def __call__(self, text: str = ""):
        print(text)
        self.lines.append(text)

    def table(self, totals: dict, title: str, limit: int = 40):
        self(f"  {title}")
        for key, amount in sorted(totals.items(), key=lambda kv: -abs(kv[1]))[:limit]:
            self(f"    {amount:>14,.2f}  {key or '(blank)'}")
        if len(totals) > limit:
            self(f"    ... {len(totals) - limit} more in the CSV")


def describe_job_fields(jobs: list[dict], say: Summary):
    """Show which job fields are actually filled in, to find where the job number lives."""
    say("\nJob fields that are filled in (sample values):")
    for field in dict.fromkeys(k for j in jobs for k in j):
        if field in ("ListID", "Sublevel", "IsActive", "Parent"):
            continue
        values = [j[field] for j in jobs if j.get(field)]
        if values:
            samples = " | ".join(dict.fromkeys(values))[:150]
            say(f"  {field:<28} {len(values):>5} filled   e.g. {samples}")


def txn_detail(session: Session, job: dict) -> qbxml.Report:
    try:
        return qbxml.parse_report(session.request(qbxml.job_txn_detail_query(job["FullName"])))
    except QBError as e:
        print(f"  (full column set refused: {e}; retrying with basic columns)")
        return qbxml.parse_report(session.request(qbxml.job_txn_detail_query(job["FullName"], qbxml.MINIMAL_COLUMNS)))


def dump_job(session: Session, job: dict, account_types: dict, say: Summary):
    safe = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in job["FullName"])[:80]
    say(f"\n=== {job['FullName']} ===")

    report = txn_detail(session, job)
    if report.rows:
        write_csv(f"job {safe} - transactions.csv", report.rows)
    say(f"  {len(report.rows)} transaction lines (columns: {', '.join(report.columns)})")

    groups = {k: defaultdict(float) for k in ("Account", "TxnType", "Item", "PayrollItem", "Class")}
    for row in report.rows:
        amount = to_float(row.get("Amount", ""))
        account = row.get("Account", "")
        groups["Account"][f"{account}  [{account_types.get(account.lower(), '?')}]"] += amount
        for k in ("TxnType", "Item", "PayrollItem", "Class"):
            if k in row:
                groups[k][row[k]] += amount
    for k, totals in groups.items():
        if totals and any(totals):
            say()
            say.table(totals, f"Totals by {k}:")

    try:
        prof = qbxml.parse_report(session.request(qbxml.job_profitability_query(job["FullName"])))
        if prof.rows or prof.totals:
            write_csv(f"job {safe} - QB job profitability.csv", prof.rows + prof.totals)
            say(f"\n  QuickBooks' own '{prof.title}' report:")
            for r in prof.rows + prof.totals:
                say("    " + "  ".join(f"{v}" for v in r.values() if v))
    except QBError as e:
        say(f"  (Job Profitability report not available: {e})")


def main(searches: list[str]):
    OUT.mkdir(exist_ok=True)
    say = Summary()
    with Session() as session:
        host = qbxml.parse_host(session.request(qbxml.host_query()))
        say(f"QuickBooks: {host['product']} {host['major']}.{host['minor']} ({host['country']})")
        say(f"qbXML versions supported: {', '.join(host['qbxml_versions'])}")

        customers = qbxml.parse_customers(session.request(qbxml.customer_query()))
        jobs = [c for c in customers if c["Sublevel"] not in ("", "0")]
        write_csv("customers_and_jobs.csv", customers)
        say(f"\n{len(customers)} customers/jobs in QuickBooks; {len(jobs)} are jobs under a customer.")
        say("Sample job names:")
        for j in (jobs or customers)[:15]:
            say(f"  {j['FullName']}")
        describe_job_fields(jobs or customers, say)

        accounts = qbxml.parse_accounts(session.request(qbxml.account_query()))
        write_csv("accounts.csv", accounts)
        account_types = {}
        for a in accounts:
            account_types[a["FullName"].lower()] = a["AccountType"]
            if a["AccountNumber"]:  # reports may show "5000 · Name"
                account_types[f"{a['AccountNumber']} · {a['FullName']}".lower()] = a["AccountType"]
        say(f"\n{len(accounts)} accounts. Cost-type accounts:")
        for a in accounts:
            if a["AccountType"] in ("CostOfGoodsSold", "Expense", "OtherExpense") and a["IsActive"] != "false":
                say(f"  {a['AccountType']:<16} {a['AccountNumber']:>6}  {a['FullName']}")

        items = qbxml.parse_items(session.request(qbxml.item_query()))
        write_csv("items.csv", items)
        say(f"\n{len(items)} items (see items.csv for which account each one posts to).")

        for search in searches:
            matches = [c for c in customers if search.lower() in c["FullName"].lower()]
            if not matches:
                say(f"\nNo customer/job matches '{search}'.")
            for job in matches[:5]:
                dump_job(session, job, account_types, say)
            if len(matches) > 5:
                say(f"\n({len(matches) - 5} more jobs match '{search}'; be more specific to see them.)")

    (OUT / "summary.txt").write_text("\n".join(say.lines), encoding="utf-8")
    print(f"\nDone. Files are in {OUT.resolve()}")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except QBError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
