"""Category I: Progress / duty notes."""

from __future__ import annotations

from scraper.endpoints import ROOT_URL, progress_note_url
from scraper.parser import parse_soup
from scraper.session import VGHSession

# Section titles in the EMR (UTF-8 encoded Chinese)
_SECTION_TITLES = {
    "病情描述(Description):": "Description",
    "主觀資料(Subjective):": "Subjective",
    "客觀資料(Objective):": "Objective",
    "診斷(Assessment):": "Assessment",
    "治療計畫(Plan):": "Plan",
}


async def fetch_progress_notes(
    session: VGHSession,
    hist_no: str,
    admin_id: str,
    num: int = 5,
) -> list[dict[str, str]]:
    """Fetch the N most recent progress notes."""
    html = await session.get(progress_note_url(hist_no, admin_id))
    soup = parse_soup(html)

    first_link = soup.find("a")
    if first_link is None or not first_link.get("href"):
        return []

    href = first_link["href"]
    if not href.startswith("http"):
        href = ROOT_URL + "/" + href.lstrip("/")

    html2 = await session.get(href)
    soup2 = parse_soup(html2)

    table = soup2.find("table")
    if table is None:
        return []
    tbody = table.find("tbody")
    if tbody is None:
        return []

    rows = tbody.find_all("tr")
    notes: list[dict[str, str]] = []
    idx = 0

    while len(notes) < num and idx < len(rows):
        row_text = rows[idx].text.strip()
        if "Note" not in row_text and "Summary" not in row_text:
            idx += 1
            continue

        note: dict[str, str] = {"date": row_text}
        idx += 1

        for title, key in _SECTION_TITLES.items():
            # Scan forward to find the title row
            while idx < len(rows) - 1:
                if title in rows[idx].text:
                    idx += 1
                    if idx < len(rows):
                        pre = rows[idx].find("pre")
                        note[key] = pre.text.strip() if pre else rows[idx].text.strip()
                    break
                idx += 1
                # If we've gone past all titles, stop
                if idx >= len(rows) - 1:
                    break

        notes.append(note)
        if idx < len(rows) - 1:
            idx += 1
        else:
            break

    return notes
