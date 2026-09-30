
import csv
import sys

with open(sys.argv[1]) as csv_file:
    reader = csv.reader(csv_file)
    next(reader) #Skip First Line
    for row in reader:
        original = row[0].replace("\n",'\\n').replace("\t",'\\t')
        simplified = row[1].replace("\n",'\\n').replace("\t",'\\t')
        print(original + "\t" + simplified)
