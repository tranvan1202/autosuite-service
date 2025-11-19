# root/engine/utils/report/excel_writer.py
"""Simple Excel exporter (phase 2 ready)."""
# Why: hiring managers love a tangible export, even if minimal.

from __future__ import annotations

from collections.abc import Iterable, Mapping

import xlsxwriter


def write_rows(path: str, rows: Iterable[Mapping[str, object]]) -> None:
    """Write rows to an .xlsx with header from first row."""
    rows = list(rows)
    if not rows:
        # Create empty sheet for predictable artifacts
        wb = xlsxwriter.Workbook(path)
        wb.add_worksheet("data")
        wb.close()
        return

    headers = list(rows[0].keys())
    wb = xlsxwriter.Workbook(path)
    ws = wb.add_worksheet("data")

    for c, h in enumerate(headers):
        ws.write(0, c, h)
    for r, row in enumerate(rows, start=1):
        for c, h in enumerate(headers):
            ws.write(r, c, row.get(h))
    wb.close()
