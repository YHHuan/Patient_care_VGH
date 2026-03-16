"""Category E: Imaging / recent reports."""

from __future__ import annotations

from scraper.endpoints import ROOT_URL, recent_report_url
from scraper.parser import parse_soup
from scraper.session import VGHSession


async def fetch_recent_reports(
    session: VGHSession, hist_no: str, report_num: int = 5
) -> list[str]:
    """Fetch names of the N most recent reports (imaging, pathology, etc.)."""
    html = await session.get(recent_report_url(hist_no))
    soup = parse_soup(html)
    reslist = soup.find(id="reslist")
    if reslist is None:
        return []

    tbody = reslist.find("tbody")
    if tbody is None:
        return []

    names: list[str] = []
    for row in tbody.find_all("tr")[:report_num]:
        a = row.find("a")
        if a:
            names.append(a.text.strip())
    return names
