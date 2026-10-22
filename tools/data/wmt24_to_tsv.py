
import json
import sys

for line in sys.stdin:
    document = json.loads(line)
    source = document['source'].replace("\n", '\\n')
    target = document['target'].replace("\n", '\\n')
    print(f"{source}\t{target}")
