"""Every QuickBooks connector must behave the same way. Add the Desktop connector here once it
exists (it can only run on a PC with QuickBooks, so mark it to skip elsewhere)."""

import pytest

from app.qb.base import QBCost, QBJob
from app.qb.fake import FakeConnector

CONNECTORS = [pytest.param(FakeConnector, id="fake")]


@pytest.fixture(params=CONNECTORS)
def connector(request):
    return request.param()


def a_job(connector) -> QBJob:
    jobs = connector.find_jobs("24-1")
    assert jobs, "connector should find at least one job for a common search"
    return jobs[0]


def test_find_jobs_returns_qbjobs(connector):
    for j in connector.find_jobs("24-1"):
        assert isinstance(j, QBJob)
        assert j.list_id and j.full_name and j.customer


def test_blank_search_finds_nothing(connector):
    assert connector.find_jobs("  ") == []


def test_get_job_round_trips_and_unknown_is_none(connector):
    job = a_job(connector)
    assert connector.get_job(job.list_id) == job
    assert connector.get_job("no-such-list-id") is None


def test_job_costs_are_qbcosts_with_numeric_amounts(connector):
    costs = connector.job_costs(a_job(connector).list_id)
    assert all(isinstance(c, QBCost) and isinstance(c.amount, float) and c.account for c in costs)


def test_job_invoiced_is_a_number(connector):
    assert isinstance(connector.job_invoiced(a_job(connector).list_id), float)
