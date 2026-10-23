"""qbXML request/response handling, tested with canned QuickBooks responses (no QB needed)."""

import xml.etree.ElementTree as ET

import pytest

from app.qb import qbxml

HOST = """<?xml version="1.0" ?><QBXML><QBXMLMsgsRs>
<HostQueryRs requestID="1" statusCode="0" statusSeverity="Info" statusMessage="Status OK">
<HostRet><ProductName>QuickBooks Enterprise Solutions: Contractor 24.0</ProductName><MajorVersion>34</MajorVersion>
<MinorVersion>0</MinorVersion><Country>US</Country><SupportedQBXMLVersion>13.0</SupportedQBXMLVersion>
<SupportedQBXMLVersion>16.0</SupportedQBXMLVersion></HostRet></HostQueryRs></QBXMLMsgsRs></QBXML>"""

CUSTOMERS = """<QBXML><QBXMLMsgsRs><CustomerQueryRs requestID="1" statusCode="0">
<CustomerRet><ListID>80000001-1</ListID><Name>Hillside Church</Name><FullName>Hillside Church</FullName>
<IsActive>true</IsActive><Sublevel>0</Sublevel></CustomerRet>
<CustomerRet><ListID>80000002-1</ListID><Name>24-117 Hall</Name><FullName>Hillside Church:24-117 Hall</FullName>
<IsActive>true</IsActive><ParentRef><FullName>Hillside Church</FullName></ParentRef><Sublevel>1</Sublevel>
<JobStatus>InProgress</JobStatus><JobTypeRef><FullName>Commercial</FullName></JobTypeRef>
<DataExtRet><OwnerID>0</OwnerID><DataExtName>Job Number</DataExtName><DataExtType>STR255TYPE</DataExtType>
<DataExtValue>24-117</DataExtValue></DataExtRet></CustomerRet>
</CustomerQueryRs></QBXMLMsgsRs></QBXML>"""

ACCOUNTS = """<QBXML><QBXMLMsgsRs><AccountQueryRs requestID="1" statusCode="0">
<AccountRet><FullName>Job Materials</FullName><IsActive>true</IsActive><AccountType>CostOfGoodsSold</AccountType>
<AccountNumber>5100</AccountNumber></AccountRet>
<AccountRet><FullName>Checking</FullName><IsActive>true</IsActive><AccountType>Bank</AccountType></AccountRet>
</AccountQueryRs></QBXMLMsgsRs></QBXML>"""

ITEMS = """<QBXML><QBXMLMsgsRs><ItemQueryRs requestID="1" statusCode="0">
<ItemServiceRet><FullName>Labor</FullName><IsActive>true</IsActive><SalesAndPurchase>
<IncomeAccountRef><FullName>Construction Income</FullName></IncomeAccountRef>
<ExpenseAccountRef><FullName>Direct Labor</FullName></ExpenseAccountRef></SalesAndPurchase></ItemServiceRet>
<ItemNonInventoryRet><FullName>Lumber</FullName><IsActive>true</IsActive><SalesOrPurchase>
<AccountRef><FullName>Job Materials</FullName></AccountRef></SalesOrPurchase></ItemNonInventoryRet>
</ItemQueryRs></QBXMLMsgsRs></QBXML>"""

REPORT = """<QBXML><QBXMLMsgsRs><CustomDetailReportQueryRs requestID="1" statusCode="0">
<ReportRet><ReportTitle>Custom Transaction Detail Report</ReportTitle><NumRows>3</NumRows><NumColumns>4</NumColumns>
<ColDesc colID="1" dataType="STRTYPE"><ColTitle titleRow="1" value="Type"/><ColType>TxnType</ColType></ColDesc>
<ColDesc colID="2" dataType="STRTYPE"><ColTitle titleRow="1" value="Name"/><ColType>Name</ColType></ColDesc>
<ColDesc colID="3" dataType="STRTYPE"><ColTitle titleRow="1" value="Account"/><ColType>Account</ColType></ColDesc>
<ColDesc colID="4" dataType="AMTTYPE"><ColTitle titleRow="1" value="Amount"/><ColType>Amount</ColType></ColDesc>
<ReportData>
<DataRow rowNumber="1"><ColData colID="1" value="Bill"/><ColData colID="2" value="Hillside Church:24-117 Hall"/>
<ColData colID="3" value="5100 · Job Materials"/><ColData colID="4" value="1,250.50"/></DataRow>
<DataRow rowNumber="2"><ColData colID="1" value="Paycheck"/><ColData colID="2" value="Hillside Church:24-117 Hall"/>
<ColData colID="3" value="Direct Labor"/><ColData colID="4" value="800.00"/></DataRow>
<TotalRow rowNumber="3"><ColData colID="1" value="TOTAL"/><ColData colID="4" value="2,050.50"/></TotalRow>
</ReportData></ReportRet></CustomDetailReportQueryRs></QBXMLMsgsRs></QBXML>"""

ERROR = """<QBXML><QBXMLMsgsRs><CustomDetailReportQueryRs requestID="1" statusCode="3120" statusSeverity="Error"
statusMessage="Object not found"/></QBXMLMsgsRs></QBXML>"""


def test_requests_are_well_formed_xml_and_escape_names():
    req = qbxml.job_txn_detail_query("Smith & Sons:24-117 <Shop>")
    root = ET.fromstring(req.split("?>", 2)[2])  # skip the two processing instructions
    assert root.find(".//ReportEntityFilter/FullName").text == "Smith & Sons:24-117 <Shop>"
    assert len(root.findall(".//IncludeColumn")) == len(qbxml.TXN_DETAIL_COLUMNS)
    for build in (qbxml.host_query, qbxml.customer_query, qbxml.account_query, qbxml.item_query):
        ET.fromstring(build().split("?>", 2)[2])


def test_requests_are_read_only():
    reqs = [qbxml.host_query(), qbxml.customer_query(), qbxml.account_query(), qbxml.item_query(),
            qbxml.job_txn_detail_query("x"), qbxml.job_profitability_query("x")]
    for r in reqs:
        assert "Add" not in r and "Mod" not in r and "Del" not in r


def test_parse_host():
    h = qbxml.parse_host(HOST)
    assert h["product"].endswith("Contractor 24.0")
    assert h["qbxml_versions"] == ["13.0", "16.0"]


def test_parse_customers_includes_custom_fields():
    cs = qbxml.parse_customers(CUSTOMERS)
    job = cs[1]
    assert job["FullName"] == "Hillside Church:24-117 Hall"
    assert job["Parent"] == "Hillside Church"
    assert job["JobType"] == "Commercial"
    assert job["Custom: Job Number"] == "24-117"


def test_parse_accounts_and_items():
    assert qbxml.parse_accounts(ACCOUNTS)[0] == {
        "FullName": "Job Materials", "AccountType": "CostOfGoodsSold", "AccountNumber": "5100", "IsActive": "true"}
    labor, lumber = qbxml.parse_items(ITEMS)
    assert (labor["Type"], labor["ExpenseAccount"], labor["IncomeAccount"]) == ("Service", "Direct Labor", "Construction Income")
    assert (lumber["Type"], lumber["Account"]) == ("NonInventory", "Job Materials")


def test_parse_report_rows_and_totals():
    r = qbxml.parse_report(REPORT)
    assert r.columns == ["Type", "Name", "Account", "Amount"]
    assert len(r.rows) == 2 and r.rows[0]["Account"] == "5100 · Job Materials"
    assert qbxml.to_float(r.rows[0]["Amount"]) == 1250.50
    assert r.totals[0]["_row"] == "TotalRow"


def test_error_status_raises():
    with pytest.raises(qbxml.QBError, match="Object not found"):
        qbxml.parse_report(ERROR)


def test_discovery_script_end_to_end(tmp_path, monkeypatch):
    from scripts import qb_discover

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            pass

        def request(self, xml):
            for tag, resp in (("HostQueryRq", HOST), ("CustomerQueryRq", CUSTOMERS), ("AccountQueryRq", ACCOUNTS),
                              ("ItemQueryRq", ITEMS), ("CustomDetailReportQueryRq", REPORT)):
                if tag in xml:
                    return resp
            return ERROR  # job profitability: exercise the error path

    monkeypatch.setattr(qb_discover, "Session", FakeSession)
    monkeypatch.setattr(qb_discover, "OUT", tmp_path)
    qb_discover.main(["24-117"])

    summary = (tmp_path / "summary.txt").read_text(encoding="utf-8")
    assert "Contractor 24.0" in summary
    assert "Custom: Job Number" in summary
    assert "5100 · Job Materials  [CostOfGoodsSold]" in summary
    assert "Job Profitability report not available" in summary
    assert (tmp_path / "accounts.csv").exists()
    assert any("transactions.csv" in p.name for p in tmp_path.iterdir())
