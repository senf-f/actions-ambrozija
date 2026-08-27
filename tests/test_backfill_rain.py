import pytest

openpyxl = pytest.importorskip("openpyxl")  # local-only backfill dep

from src.backfill_rain import parse_sheet


def _sheet():
    """One 2025 block: Jan has data, Feb is '-' (no data), Mar has a '*' day."""
    ws = openpyxl.Workbook().active
    ws.cell(8, 1, 2025)
    for col, roman in enumerate(['I', 'II', 'III'], start=2):
        ws.cell(8, col, roman)
    ws.cell(8 + 1, 2, 5.5)      # 1 Jan
    ws.cell(8 + 2, 2, 0)        # 2 Jan explicit zero
    # 3-31 Jan left blank -> 0.0
    ws.cell(8 + 1, 3, 9.9)      # 1 Feb, but month is marked '-' so it's ignored
    ws.cell(8 + 1, 4, 2.0)      # 1 Mar
    ws.cell(8 + 2, 4, '*')      # 2 Mar not measured
    ws.cell(8 + 33, 2, 5.5)     # ZBROJ Jan
    ws.cell(8 + 33, 3, '-')     # ZBROJ Feb: no data
    ws.cell(8 + 33, 4, 2.0)     # ZBROJ Mar
    return ws


def test_parse_sheet():
    rows = dict(parse_sheet(_sheet()))

    assert rows['2025-01-01'] == 5.5
    assert rows['2025-01-02'] == 0.0
    assert rows['2025-01-15'] == 0.0          # blank means no rain
    assert sum(v for k, v in rows.items() if k.startswith('2025-01')) == 5.5
    assert len([k for k in rows if k.startswith('2025-01')]) == 31

    assert not [k for k in rows if k.startswith('2025-02')]  # '-' month skipped

    assert rows['2025-03-01'] == 2.0
    assert '2025-03-02' not in rows           # '*' day skipped
    assert '2025-03-32' not in rows           # never past month length
