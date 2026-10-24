"""Cost buckets and statuses: the business vocabulary shared by the math, sync, API and export."""

BUCKETS = ("labor", "material", "sub", "misc")

BUCKET_LABELS = {
    "labor": "Labor",
    "material": "Material",
    "sub": "Subcontractor",
    "misc": "Direct expenses / misc",
}

# QB accounts that aren't mapped to a bucket count as direct expenses / misc
UNMAPPED_BUCKET = "misc"

STATUS_LABELS = {"ok": "On track", "trending": "Trending over", "over": "Over budget"}
STATUS_RANK = {"ok": 0, "trending": 1, "over": 2}
