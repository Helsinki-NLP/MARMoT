import csv
import sys

# Change these to the three columns you want.
COLUMNS = ["word","pos","gloss","example"]

reader = csv.DictReader(sys.stdin)
writer = csv.DictWriter(
    sys.stdout,
    fieldnames=COLUMNS,
    delimiter="\t",
    extrasaction="ignore",
)

writer.writeheader()

for row in reader:
    writer.writerow({col: row[col] for col in COLUMNS})

