"""Fetch patient list by doctor code, ward, or chart number."""

from __future__ import annotations

import logging

from scraper.endpoints import MY_PATIENTS, patient_search_url
from scraper.parser import parse_soup
from scraper.session import VGHSession

logger = logging.getLogger(__name__)


async def fetch_patient_list(session: VGHSession) -> list[list[str]]:
    """Fetch current user's patient list (my patients)."""
    html = await session.get(MY_PATIENTS)
    soup = parse_soup(html)
    table = soup.find(id="patlist")
    if table is None:
        return []

    tbody = table.find("tbody")
    if tbody is None:
        return []

    data: list[list[str]] = []
    for row in tbody.find_all("tr"):
        cols = [td.text.strip() for td in row.find_all("td")]
        cols = [c for c in cols if c]
        if cols and len(cols) >= 2:
            # Strip "New" prefix (senior's pattern)
            if "New" in cols[1]:
                cols[1] = cols[1][3:]
            data.append(cols)
    return data


async def fetch_searched_patients(
    session: VGHSession,
    *,
    ward: str = "0",
    hist_no: str = "",
    doc_id: str = "",
) -> list[list[str]]:
    """Search patients by ward / chart number / doctor ID."""
    url = patient_search_url(ward=ward, hist_no=hist_no, doc_id=doc_id)
    html = await session.get(url)
    soup = parse_soup(html)
    table = soup.find("table")
    if table is None:
        return []

    tbody = table.find("tbody")
    if tbody is None:
        return []

    data: list[list[str]] = []
    for row in tbody.find_all("tr"):
        cols = [td.text.strip() for td in row.find_all("td")]
        # Clean up (senior's pattern)
        if len(cols) > 2 and "(N)" in cols[2]:
            cols[2] = cols[2][4:].replace("\xa0", "")
        if ward != "0" and len(cols) > 1:
            cols[1] = cols[1].split("[")[0]
        cols = cols[1:]  # drop first column
        data.append(cols)
    return data
