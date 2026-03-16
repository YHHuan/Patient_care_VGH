"""HTML table → DataFrame parsers (senior's patterns)."""

from __future__ import annotations

import pandas as pd
from bs4 import BeautifulSoup, Tag


def html_table(soup_or_table: Tag) -> pd.DataFrame:
    """Standard thead+tbody table → DataFrame (senior's html_table)."""
    thead = soup_or_table.find("thead")
    headers = [th.text.strip() for th in thead.find_all("th")] if thead else []

    tbody = soup_or_table.find("tbody")
    rows: list[list[str]] = []
    if tbody:
        for tr in tbody.find_all("tr"):
            cols = [td.text.strip() for td in tr.find_all("td")]
            cols = [c for c in cols if c]
            if cols:
                rows.append(cols)

    return pd.DataFrame(rows, columns=headers if headers else None)


def html_res_table(table: Tag) -> pd.DataFrame:
    """Lab result table — skip last row (senior's html_res_table)."""
    thead = table.find("thead")
    headers = [th.text.strip() for th in thead.find_all("th")] if thead else []

    tbody = table.find("tbody")
    rows: list[list[str]] = []
    if tbody:
        all_tr = tbody.find_all("tr")
        for tr in all_tr[:-1]:  # skip last row
            cols = [td.text.strip() for td in tr.find_all("td")]
            rows.append(cols)

    return pd.DataFrame(rows, columns=headers if headers else None)


def html_report_table(table: Tag) -> pd.DataFrame:
    """Report table — no thead, just tbody rows (senior's html_report_table)."""
    tbody = table.find("tbody")
    rows: list[list[str]] = []
    if tbody:
        for tr in tbody.find_all("tr"):
            cols = [td.text.strip() for td in tr.find_all("td")]
            if cols != [""]:
                rows.append(cols)
    df = pd.DataFrame(rows)
    return df.dropna()


def html_io_table(table: Tag) -> pd.DataFrame | None:
    """I/O drainage table (senior's html_IO_table)."""
    all_rows = table.find_all("tr")
    drainage_row = None
    for row in all_rows:
        first_td = row.find("td")
        if first_td and "引流" in first_td.text:
            drainage_row = row
            break

    if drainage_row is None:
        return None

    inner_table = drainage_row.find("table")
    if inner_table is None:
        return None

    data: list[list[str]] = []
    for tr in inner_table.find_all("tr"):
        cols = [td.text.strip() for td in tr.find_all("td")]
        data.append(cols)

    return pd.DataFrame(data, columns=["項目", "白班", "小夜", "大夜", "總量"])


def admin_intro_table(table: Tag) -> pd.DataFrame:
    """Admission intro table (senior's admin_Intro_table)."""
    tbody = table.find("tbody")
    cols_head: list[str] = []
    data: list[str] = []
    if tbody:
        for tr in tbody.find_all("tr"):
            tds = [td.text.strip() for td in tr.find_all("td")]
            if len(tds) >= 2:
                label = tds[0]
                # strip leading number + dot: "１．主訴:" → "主訴"
                if "．" in label:
                    label = label.split("．", 1)[1].rstrip(":")
                cols_head.append(label)
                data.append(tds[1])
    return pd.DataFrame([data], columns=cols_head)


def parse_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")
