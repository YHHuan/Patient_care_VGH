"""Category H: Admission notes."""

from __future__ import annotations

from scraper.endpoints import ROOT_URL, admission_url
from scraper.parser import parse_soup
from scraper.session import VGHSession


async def fetch_last_admission(session: VGHSession, hist_no: str) -> str:
    """Fetch the most recent admission note text."""
    html = await session.get(admission_url(hist_no))
    soup = parse_soup(html)

    adm_link = soup.find(title="admnote")
    if adm_link is None or not adm_link.get("href"):
        return ""

    href = adm_link["href"]
    if not href.startswith("http"):
        href = ROOT_URL + "/" + href.lstrip("/")

    html2 = await session.get(href)
    soup2 = parse_soup(html2)
    pre = soup2.find("pre")
    return pre.text.strip() if pre else ""
