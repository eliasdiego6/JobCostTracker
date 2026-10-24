"""QuickBooks connectors. This is the only place that knows which QB mode is active."""

from app import config
from app.qb.base import Connector


def get_connector() -> Connector:
    mode = config.qb_mode()
    if mode == "fake":
        from app.qb.fake import FakeConnector

        return FakeConnector()
    if mode == "desktop":
        raise NotImplementedError(
            "QuickBooks Desktop connector is built in step 3 (needs the QB version first)."
        )
    raise ValueError(f"Unknown JCT_QB_MODE: {mode!r}")


def default_account_map() -> dict[str, str]:
    """Account -> bucket map to start with on a new database. Real QB mappings are set in Settings."""
    if config.qb_mode() == "fake":
        from app.qb.fake import DEFAULT_ACCOUNT_MAP

        return dict(DEFAULT_ACCOUNT_MAP)
    return {}
