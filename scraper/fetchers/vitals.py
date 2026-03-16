"""Category B: Vitals (TPR) + body weight/height."""

from __future__ import annotations

import pandas as pd

from scraper.endpoints import bw_bl_url, tpr_url
from scraper.parser import html_table, parse_soup
from scraper.session import VGHSession


async def fetch_tpr(session: VGHSession, hist_no: str, admin_id: str) -> pd.DataFrame:
    """Fetch TPR (temperature, pulse, respiration, BP) table."""
    html = await session.get(tpr_url(admin_id))
    soup = parse_soup(html)
    table = soup.find(id="tprlist")
    if table is None:
        # Fallback: any table on page
        table = soup.find("table")
    if table is None:
        return pd.DataFrame()
    return html_table(table)


async def fetch_bw_bl(
    session: VGHSession, hist_no: str, admin_id: str = "all"
) -> pd.DataFrame:
    """Fetch body weight / height records."""
    html = await session.get(bw_bl_url(hist_no, admin_id))
    soup = parse_soup(html)
    table = soup.find("table")
    if table is None:
        return pd.DataFrame()
    return html_table(table)
