"""Category G: Operation / procedure records."""

from __future__ import annotations

from scraper.endpoints import ROOT_URL, op_url
from scraper.parser import parse_soup
from scraper.session import VGHSession


async def fetch_op(session: VGHSession, hist_no: str) -> dict[str, str]:
    """Fetch most recent operation record."""
    html = await session.get(op_url(hist_no))
    soup = parse_soup(html)

    a = soup.find("a")
    if a is None or not a.get("href"):
        return {}

    href = a["href"]
    if not href.startswith("http"):
        href = ROOT_URL + "/" + href.lstrip("/")

    html2 = await session.get(href)
    soup2 = parse_soup(html2)
    table = soup2.find("table")
    if table is None:
        return {}

    tbody = table.find("tbody")
    if tbody is None:
        return {}

    rows = tbody.find_all("tr")
    result: dict[str, str] = {}
    try:
        if len(rows) > 6:
            tds = rows[6].find_all("td")
            if len(tds) > 3:
                result["Anes"] = tds[3].text.strip()
        if len(rows) > 7:
            tds = rows[7].find_all("td")
            if len(tds) > 1:
                result["OP_Dx"] = tds[1].text.strip()
        if len(rows) > 8:
            tds = rows[8].find_all("td")
            if len(tds) > 1:
                result["OP_name"] = tds[1].text.strip()
    except (IndexError, AttributeError):
        pass

    return result
