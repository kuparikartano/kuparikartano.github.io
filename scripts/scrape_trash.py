"""Fetch trash pickup dates from HSY and write _data/trash.json.

The SPA at
  https://raportit.hsy.fi/report/#/fi/serviceDescription/<service>/<postal>/<customer>////
loads its data from this undocumented but unauthenticated endpoint:
  https://raportit.hsy.fi/report/ajax-open/stats/description/waste/<service>/<postal>/<customer>/<lang>

Jekyll picks the JSON file up via `site.data.trash` exactly like it would a
.yml file, so the templates don't care which format we use.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path

import requests

# --- config (override via env vars or CLI args) -----------------------------

DEFAULT_SERVICE  = "BB11-012731-0"
DEFAULT_POSTAL   = "00410"
DEFAULT_CUSTOMER = "72603608934"
DEFAULT_LANG     = "fi"

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "_data" / "trash.json"

WEEKDAYS_FI = ["ma", "ti", "ke", "to", "pe", "la", "su"]
_DATE_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{2,4})$")


# --- helpers ----------------------------------------------------------------

def parse_finnish_date(raw):
    """'22.5.2026' or '23.10.18' → datetime.date, or None."""
    m = _DATE_RE.match((raw or "").strip())
    if not m:
        return None
    d, mo, y = (int(x) for x in m.groups())
    if y < 100:
        y += 2000
    try:
        return dt.date(y, mo, d)
    except ValueError:
        return None


def walk_containers(node, address):
    """Yield container dicts from anywhere in the response. `address` is a
    one-element list used as a mutable holder for the collection address."""
    if isinstance(node, dict):
        for key in ("wasteCollectionAddress", "address"):
            v = node.get(key)
            if isinstance(v, str) and "," in v and not address:
                address.append(v)
        if "nextCollectionDate" in node or ("wasteType" in node and "containerSize" in node):
            yield node
        for v in node.values():
            yield from walk_containers(v, address)
    elif isinstance(node, list):
        for item in node:
            yield from walk_containers(item, address)


def to_container_dict(raw):
    today = dt.date.today()
    out = {
        "waste_type":          (raw.get("wasteType") or "").strip(),
        "container_size":      (raw.get("containerSize") or "").strip(),
        "container_count":     (raw.get("containerCount") or "").strip(),
        "container_type":      (raw.get("containerType") or "").strip(),
        "container_owner":     (raw.get("containerOwner") or "").strip(),
        "collection_interval": (raw.get("collectionInterval") or "").strip(),
        "next_collection_date":       "",
        "next_collection_date_human": "",
        "next_collection_date_short": "",
        "days_until": None,
        "is_next": False,
    }
    d = parse_finnish_date(raw.get("nextCollectionDate") or "")
    if d:
        out["next_collection_date"]       = d.isoformat()
        out["next_collection_date_human"] = f"{WEEKDAYS_FI[d.weekday()]} {d.day}.{d.month}.{d.year}"
        out["next_collection_date_short"] = f"{d.day:02d}.{d.month:02d}.{d.year % 100:02d}"
        out["days_until"] = (d - today).days
    return out


# --- main -------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--service",  default=os.getenv("HSY_SERVICE",  DEFAULT_SERVICE))
    ap.add_argument("--postal",   default=os.getenv("HSY_POSTAL",   DEFAULT_POSTAL))
    ap.add_argument("--customer", default=os.getenv("HSY_CUSTOMER", DEFAULT_CUSTOMER))
    ap.add_argument("--lang",     default=os.getenv("HSY_LANG",     DEFAULT_LANG))
    ap.add_argument("--out",      default=str(DATA_FILE))
    args = ap.parse_args()

    api_url = (
        "https://raportit.hsy.fi/report/ajax-open/stats/description/waste/"
        f"{args.service}/{args.postal}/{args.customer}/{args.lang}"
    )
    spa_url = (
        "https://raportit.hsy.fi/report/#/fi/serviceDescription/"
        f"{args.service}/{args.postal}/{args.customer}/"
    )

    print(f"GET {api_url}")
    resp = requests.get(
        api_url,
        headers={
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fi,en;q=0.8",
            "Referer": "https://raportit.hsy.fi/report/",
            "User-Agent": "trash-scraper/1.0 (+github actions)",
        },
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()

    address = []
    seen = set()
    containers = []
    for raw in walk_containers(payload, address):
        key = (raw.get("wasteType"), raw.get("containerSize"),
               raw.get("containerType"), raw.get("collectionInterval"),
               raw.get("nextCollectionDate"))
        if key in seen:
            continue
        seen.add(key)

        # skip liner-bag entries (säkki lives inside an astia, not a separate collection)
        if (raw.get("containerType") or "").strip() != "säkki":
            containers.append(to_container_dict(raw))

    if not containers:
        raise RuntimeError("No container records found in the JSON response.")

    # Mark the soonest upcoming pickup
    upcoming = sorted(
        [c for c in containers if c["days_until"] is not None and c["days_until"] >= 0],
        key=lambda c: c["days_until"],
    )
    nxt = None
    if upcoming:
        upcoming[0]["is_next"] = True
        nxt = upcoming[0]

    # Sort everything: pickups with a date first (soonest first), rest after
    containers.sort(key=lambda c: (c["days_until"] is None, c["days_until"] or 0, c["waste_type"]))

    now_utc = dt.datetime.now(dt.timezone.utc)
    helsinki = now_utc + dt.timedelta(hours=3 if 3 <= now_utc.month <= 10 else 2)

    out = {
        "updated_at": now_utc.isoformat(timespec="seconds"),
        "updated_at_human": f"{helsinki.day}.{helsinki.month}.{helsinki.year} klo {helsinki.strftime('%H:%M')}",
        "source_url": spa_url,
        "collection_address": address[0] if address else "",
        "containers": containers,
        "next": nxt,
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"OK — {len(containers)} container(s); next = "
          f"{nxt['waste_type'] if nxt else '?'} "
          f"{nxt['next_collection_date_short'] if nxt else ''}")


if __name__ == "__main__":
    main()
