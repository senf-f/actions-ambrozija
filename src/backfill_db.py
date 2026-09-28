"""One-time script to parse all CSV/data files in data/ and insert into SQLite."""
import os
import re

from src.db_handler import setup_db
from src.pollen_record import DATA_DIR, UPSERT, parse_filename

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def parse_line(line):
    """Return (concentration_str, date_str) or None."""
    line = line.strip()
    if not line or line.startswith('pollen_concentration'):
        return None

    # Space-separated: "1.9  2022-10-01  13:13:23.138972"
    parts = line.split()
    if len(parts) >= 2 and is_float(parts[0]) and DATE_RE.match(parts[1]):
        return parts[0], parts[1]

    # Comma-separated with city: "Dubrovnik,CEMPRESI,0.5,2025-10-31T15:10:27"
    if ',' in line:
        fields = line.split(',')
        if len(fields) == 4 and is_float(fields[2]):
            date_str = fields[3][:10]
            if DATE_RE.match(date_str):
                return fields[2], date_str
        # Without city: "0.5,2025-10-31T15:16:48"
        if len(fields) == 2 and is_float(fields[0]):
            date_str = fields[1][:10]
            if DATE_RE.match(date_str):
                return fields[0], date_str

    return None


def main():
    conn = setup_db()
    cursor = conn.cursor()

    stats = {'files': 0, 'rows': 0, 'skipped_files': 0, 'skipped_lines': 0}

    for root, dirs, files in os.walk(DATA_DIR):
        # Skip test directory
        if 'test' in os.path.basename(root):
            continue
        for filename in files:
            parsed = parse_filename(filename)
            if not parsed:
                stats['skipped_files'] += 1
                print(f"Skipping: {filename}")
                continue

            city, plant = parsed
            filepath = os.path.join(root, filename)

            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    result = parse_line(line)
                    if result is None:
                        stats['skipped_lines'] += 1
                        continue
                    conc, date_str = result
                    cursor.execute(UPSERT, (city, plant, conc, date_str))
                    stats['rows'] += 1

            conn.commit()
            stats['files'] += 1

    conn.close()
    print(f"\nDone. Processed {stats['files']} files, "
          f"inserted {stats['rows']} rows, "
          f"skipped {stats['skipped_files']} files, "
          f"{stats['skipped_lines']} lines.")


if __name__ == '__main__':
    main()
