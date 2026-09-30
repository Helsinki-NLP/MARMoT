
import sys
import argparse
from sacremoses import MosesDetokenizer

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--language", type=str, default="en", help="detokenization language")
args = parser.parse_args()

detokenizer = MosesDetokenizer(args.language)

for line in sys.stdin:
    print(detokenizer.detokenize(line.strip().split(),return_str=True,unescape=True))


#    parts = line.split("\t")
#    parts[0] = detokenizer.detokenize(parts[0].strip().split(),return_str=True,unescape=True)
#    parts[1] = detokenizer.detokenize(parts[1].strip().split(),return_str=True,unescape=True)
#    print("\t".join(parts))
