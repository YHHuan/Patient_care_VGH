"""Category D: Current medications."""

from __future__ import annotations

import pandas as pd

from scraper.endpoints import ROOT_URL, drug_url
from scraper.fetchers.demographics import fetch_admin_id
from scraper.parser import html_table, parse_soup
from scraper.session import VGHSession


async def fetch_drugs(
    session: VGHSession, hist_no: str, admin_id: str | None = None
) -> pd.DataFrame:
    """Fetch current drug orders for a patient."""
    if admin_id is None:
        admin_id = await fetch_admin_id(session, hist_no)

    html = await session.get(drug_url(hist_no))
    soup = parse_soup(html)

    # Find the link matching this admission's caseno
    all_links = soup.find_all("a")
    target_href = None
    for a in all_links:
        href = a.get("href", "")
        if admin_id in href:
            target_href = href
            break
    if target_href is None and all_links:
        target_href = all_links[0].get("href", "")

    if not target_href:
        return pd.DataFrame()

    if not target_href.startswith("http"):
        target_href = ROOT_URL + "/" + target_href.lstrip("/")

    html2 = await session.get(target_href)
    soup2 = parse_soup(html2)
    table = soup2.find(id="udorder")
    if table is None:
        return pd.DataFrame()
    return html_table(table)
