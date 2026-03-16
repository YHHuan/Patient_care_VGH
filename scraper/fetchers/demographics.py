"""Category A: Demographics + admin ID resolution."""

from __future__ import annotations

import logging

import pandas as pd

from scraper.endpoints import admin_id_url, admin_intro_url, emr_url
from scraper.parser import admin_intro_table, parse_soup
from scraper.session import VGHSession

logger = logging.getLogger(__name__)


async def fetch_admin_id(session: VGHSession, hist_no: str) -> str:
    """Resolve histno → caseno (adminID) needed by most endpoints."""
    # Touch EMR page first (required by server)
    await session.get(emr_url(hist_no))
    html = await session.get(admin_id_url(hist_no))
    soup = parse_soup(html)
    option = soup.find("option")
    if option and option.get("value"):
        return option["value"].split("=")[-1]
    raise ValueError(f"Could not resolve adminID for {hist_no}")


async def fetch_demographics(session: VGHSession, hist_no: str) -> pd.DataFrame:
    """Fetch admission intro (basic patient info table)."""
    html = await session.get(admin_intro_url(hist_no))
    soup = parse_soup(html)
    table = soup.find("table")
    if table is None:
        return pd.DataFrame()
    return admin_intro_table(table)
