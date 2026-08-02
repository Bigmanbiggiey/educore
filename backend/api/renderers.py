"""CSV/XLSX renderers for `analytics`'s rollup list endpoints — docs/roadmap.md
Phase 8's "Exports: PDF, Excel, CSV" (PDF export is `reports`'s job; this
covers the tabular half). Selected via DRF's standard `?format=csv|xlsx`
content negotiation — the idiomatic DRF mechanism, not a bespoke export
endpoint. Both renderers flatten a paginated list response's `results` key
if present (falling back to treating `data` as already a flat list), so
they work whether or not the view they're attached to paginates.
"""

import csv
import io

import openpyxl
from rest_framework.renderers import BaseRenderer


def _rows(data):
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    if isinstance(data, list):
        return data
    return [data]


class CSVRenderer(BaseRenderer):
    media_type = "text/csv"
    format = "csv"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        rows = _rows(data)
        if not rows:
            return b""
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue().encode("utf-8")


class XLSXRenderer(BaseRenderer):
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    format = "xlsx"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        rows = _rows(data)
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        if rows:
            headers = list(rows[0].keys())
            sheet.append(headers)
            for row in rows:
                sheet.append([str(row.get(header, "")) for header in headers])
        buffer = io.BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()
