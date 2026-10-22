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
