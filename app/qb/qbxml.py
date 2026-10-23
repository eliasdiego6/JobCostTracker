"""Talking to QuickBooks Desktop through the QB SDK (qbXML over COM).

Read-only: this module only ever sends *Query* requests. The request builders and
parsers are plain functions so they can be tested without QuickBooks installed.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from xml.sax.saxutils import escape

APP_NAME = "Job Cost Tracker"
QBXML_VERSION = "13.0"  # Enterprise 24 supports up to 16.0; 13.0 covers everything we query


class QBError(Exception):
    pass


def envelope(body: str, version: str = QBXML_VERSION) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<?qbxml version="{version}"?>'
        f'<QBXML><QBXMLMsgsRq onError="continueOnError">{body}</QBXMLMsgsRq></QBXML>'
    )


# ---------- request builders ----------


def host_query() -> str:
    return envelope('<HostQueryRq requestID="1"/>', version="1.0")


def customer_query() -> str:
    # OwnerID 0 returns the job's custom fields (where a job number might live)
    return envelope('<CustomerQueryRq requestID="1"><ActiveStatus>All</ActiveStatus><OwnerID>0</OwnerID></CustomerQueryRq>')


def account_query() -> str:
    return envelope('<AccountQueryRq requestID="1"><ActiveStatus>All</ActiveStatus></AccountQueryRq>')


def item_query() -> str:
    return envelope('<ItemQueryRq requestID="1"><ActiveStatus>All</ActiveStatus></ItemQueryRq>')


TXN_DETAIL_COLUMNS = [
    "TxnID", "TxnType", "Date", "RefNumber", "Name", "SourceName", "Account", "SplitAccount",
    "Item", "ItemDesc", "PayrollItem", "Class", "Memo", "Quantity", "Debit", "Credit", "Amount",
]
MINIMAL_COLUMNS = ["TxnType", "Date", "RefNumber", "Name", "Account", "Memo", "Amount"]


def job_txn_detail_query(job_full_name: str, columns: list[str] = TXN_DETAIL_COLUMNS) -> str:
    """Every transaction line posted to one Customer:Job, all dates."""
    cols = "".join(f"<IncludeColumn>{c}</IncludeColumn>" for c in columns)
    return envelope(
        '<CustomDetailReportQueryRq requestID="1">'
        "<CustomDetailReportType>CustomTxnDetail</CustomDetailReportType>"
        "<DisplayReport>false</DisplayReport>"
        "<ReportDateMacro>All</ReportDateMacro>"
        f"<ReportEntityFilter><FullName>{escape(job_full_name)}</FullName></ReportEntityFilter>"
        "<ReportDetailLevelFilter>All</ReportDetailLevelFilter>"
        "<SummarizeRowsBy>TotalOnly</SummarizeRowsBy>"
        f"{cols}"
        "</CustomDetailReportQueryRq>"
    )


def job_profitability_query(job_full_name: str) -> str:
    """QuickBooks' own Job Profitability Detail report, used to cross-check our totals."""
    return envelope(
        '<JobReportQueryRq requestID="1">'
        "<JobReportType>JobProfitabilityDetail</JobReportType>"
        "<DisplayReport>false</DisplayReport>"
        "<ReportDateMacro>All</ReportDateMacro>"
        f"<ReportEntityFilter><FullName>{escape(job_full_name)}</FullName></ReportEntityFilter>"
        "</JobReportQueryRq>"
    )


# ---------- response parsing ----------


def response_body(xml: str) -> ET.Element:
    """Return the single *Rs element, raising QBError if QuickBooks reported an error."""
    root = ET.fromstring(xml)
    rs = root.find("./QBXMLMsgsRs/*")
    if rs is None:
        raise QBError("Empty response from QuickBooks")
    code = int(rs.get("statusCode", "0"))
    # 1 = "no matching objects found", which just means an empty result
    if code not in (0, 1):
        raise QBError(f"{rs.tag} failed ({code}): {rs.get('statusMessage')}")
    return rs


def _text(el: ET.Element, path: str) -> str:
    found = el.find(path)
    return found.text.strip() if found is not None and found.text else ""


def parse_host(xml: str) -> dict:
    host = response_body(xml).find("HostRet")
    return {
        "product": _text(host, "ProductName"),
        "major": _text(host, "MajorVersion"),
        "minor": _text(host, "MinorVersion"),
        "country": _text(host, "Country"),
        "qbxml_versions": [v.text for v in host.findall("SupportedQBXMLVersion")],
    }


def parse_customers(xml: str) -> list[dict]:
    out = []
    for c in response_body(xml).findall("CustomerRet"):
        row = {
            "ListID": _text(c, "ListID"),
            "FullName": _text(c, "FullName"),
            "Name": _text(c, "Name"),
            "Sublevel": _text(c, "Sublevel"),
            "Parent": _text(c, "ParentRef/FullName"),
            "IsActive": _text(c, "IsActive"),
            "AccountNumber": _text(c, "AccountNumber"),
            "JobStatus": _text(c, "JobStatus"),
            "JobType": _text(c, "JobTypeRef/FullName"),
            "JobDesc": _text(c, "JobDesc"),
            "JobStartDate": _text(c, "JobStartDate"),
            "JobEndDate": _text(c, "JobEndDate"),
            "Class": _text(c, "ClassRef/FullName"),
        }
        for ext in c.findall("DataExtRet"):
            row[f"Custom: {_text(ext, 'DataExtName')}"] = _text(ext, "DataExtValue")
        out.append(row)
    return out


def parse_accounts(xml: str) -> list[dict]:
    return [
        {
            "FullName": _text(a, "FullName"),
            "AccountType": _text(a, "AccountType"),
            "AccountNumber": _text(a, "AccountNumber"),
            "IsActive": _text(a, "IsActive"),
        }
        for a in response_body(xml).findall("AccountRet")
    ]


def parse_items(xml: str) -> list[dict]:
    out = []
    for it in response_body(xml):
        if not it.tag.startswith("Item"):
            continue
        out.append(
            {
                "Type": it.tag.removeprefix("Item").removesuffix("Ret"),
                "FullName": _text(it, "FullName"),
                "IsActive": _text(it, "IsActive"),
                # purchase side of two-sided items, else the single account
                "ExpenseAccount": _text(it, ".//ExpenseAccountRef/FullName") or _text(it, ".//COGSAccountRef/FullName"),
                "Account": _text(it, ".//AccountRef/FullName"),
                "IncomeAccount": _text(it, ".//IncomeAccountRef/FullName"),
            }
        )
    return out


@dataclass
class Report:
    title: str
    columns: list[str]
    rows: list[dict]  # data rows only (no subtotals)
    totals: list[dict]  # SubtotalRow / TotalRow, for cross-checking


def parse_report(xml: str) -> Report:
    ret = response_body(xml).find("ReportRet")
    if ret is None:
        return Report("", [], [], [])
    col_names = {}
    for cd in ret.findall("ColDesc"):
        title = " ".join(t.get("value", "") for t in cd.findall("ColTitle")).strip()
        col_names[cd.get("colID")] = title or cd.findtext("ColType") or f"col{cd.get('colID')}"
    rows, totals = [], []
    data = ret.find("ReportData")
    for row in data if data is not None else []:
        values = {col_names.get(c.get("colID"), c.get("colID")): c.get("value", "") for c in row.findall("ColData")}
        if row.tag == "DataRow":
            rows.append(values)
        elif row.tag in ("SubtotalRow", "TotalRow"):
            totals.append({"_row": row.tag, **values})
    return Report(_text(ret, "ReportTitle"), list(col_names.values()), rows, totals)


def to_float(value: str) -> float:
    try:
        return float(value.replace(",", "")) if value else 0.0
    except ValueError:
        return 0.0


# ---------- the COM connection (Windows + QuickBooks only) ----------


class Session:
    """Opens a session with the running QuickBooks / company file. Use as a context manager."""

    def __init__(self, company_file: str = ""):
        self.company_file = company_file  # "" = whichever company file QuickBooks has open

    def __enter__(self):
        try:
            import win32com.client
        except ImportError as e:
            raise QBError("pywin32 is not installed: pip install pywin32") from e
        try:
            self.rp = win32com.client.Dispatch("QBXMLRP2.RequestProcessor")
        except Exception as e:
            raise QBError(
                "Could not load the QuickBooks request processor (QBXMLRP2). Run this on a PC with "
                "QuickBooks Desktop installed. If QuickBooks is installed, try 32-bit Python."
            ) from e
        self.rp.OpenConnection2("", APP_NAME, 1)  # 1 = local QuickBooks Desktop
        try:
            self.ticket = self.rp.BeginSession(self.company_file, 2)  # 2 = open in whatever mode QB is in
        except Exception as e:
            self.rp.CloseConnection()
            raise QBError(
                "QuickBooks refused the connection. Open QuickBooks and the company file, sign in as Admin, "
                "and answer the 'An application is requesting access' prompt with "
                "'Yes, always; allow access even if QuickBooks is not running'."
            ) from e
        return self

    def request(self, xml: str) -> str:
        return self.rp.ProcessRequest(self.ticket, xml)

    def __exit__(self, *exc):
        self.rp.EndSession(self.ticket)
        self.rp.CloseConnection()
