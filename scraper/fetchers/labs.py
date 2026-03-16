"""Category C: Lab results."""

from __future__ import annotations

import pandas as pd

from scraper.endpoints import LAB_REPORT_TYPES, lab_value_url, res_report_url
from scraper.parser import html_res_table, parse_soup
from scraper.session import VGHSession


async def fetch_lab_report(
    session: VGHSession,
    hist_no: str,
    report_type: str = "SMAC",
    months: str = "00",
) -> pd.DataFrame:
    """Fetch structured lab report (SMAC/CBC/Urine/Cancer)."""
    internal_type = LAB_REPORT_TYPES.get(report_type, report_type)
    html = await session.get(res_report_url(hist_no, internal_type, months))
    soup = parse_soup(html)
    table = soup.find(id="resdtable")
    if table is None:
        return pd.DataFrame()
    return html_res_table(table)


async def fetch_lab_value(
    session: VGHSession,
    hist_no: str,
    lab_name: str,
    months: str = "24",
) -> list[list[str]]:
    """Fetch individual lab value trend (e.g. CRP over time)."""
    html = await session.get(lab_value_url(hist_no, months=months))
    soup = parse_soup(html)
    elem = soup.find(id=lab_name)
    if elem is None:
        return []
    time_list = elem.text.split("|")
    return [entry.split("/") for entry in time_list]
