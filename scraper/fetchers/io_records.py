"""Category F: I/O (intake/output) records — drainage."""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from scraper.endpoints import nis_io_detail_url, nis_io_url
from scraper.parser import html_io_table, parse_soup
from scraper.session import VGHSession


async def fetch_drainage(
    session: VGHSession, hist_no: str, admin_id: str
) -> pd.DataFrame | None:
    """Fetch yesterday's drainage I/O table from NIS."""
    # Step 1: enter NIS context for this patient
    await session.get(nis_io_url(hist_no, admin_id))

    # Step 2: fetch yesterday's I/O detail
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    html = await session.get(nis_io_detail_url(yesterday))
    soup = parse_soup(html)

    div = soup.find(id="divshow_0")
    if div is None:
        return None

    # Navigate: div → table → table → tables[1]
    outer = div.find("table")
    if outer is None:
        return None
    inner = outer.find("table")
    if inner is None:
        return None
    all_tables = inner.find_all("table")
    if len(all_tables) < 2:
        return None

    return html_io_table(all_tables[1])
