# root/engine/utils/report/html_writer.py
"""Minimal HTML exporter."""
# Why: quick human preview without Excel installed.

from __future__ import annotations

from collections.abc import Iterable, Mapping


def write_rows(path: str, rows: Iterable[Mapping[str, object]]) -> None:
    """Dump a simple table with inline styles."""
    rows = list(rows)
    headers = list(rows[0].keys()) if rows else []
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            "<html><head><meta charset='utf-8'><style>table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:4px}</style></head><body>"
        )
        f.write("<table>")
        if headers:
            f.write("<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>")
        for row in rows:
            f.write("<tr>" + "".join(f"<td>{row.get(h,'')}</td>" for h in headers) + "</tr>")
        f.write("</table></body></html>")
