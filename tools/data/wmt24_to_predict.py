
import json
import argparse
import sys

from loomchild.segmenter import LoomchildSegmenter

parser = argparse.ArgumentParser(description='fetch fineweb data and prepare for translation')
parser.add_argument('-i', '--input-file', help='input-file', type=str)
parser.add_argument('-l', '--lang', help='language (default=en)', type=str, default='en')
parser.add_argument('-f', '--field', help='json field (default=source)', type=str, default='source')
args = parser.parse_args()


lang = args.lang
field = args.field

## segmenter for splitting into sentences
segmenter = LoomchildSegmenter(lang)


with open(args.input_file) as f:
    for line in f:
        document = json.loads(line)
        sents = segmenter.get_document_segmentation(document[field])
        prev = ""
        for sent in sents:
            if prev:
                print(f"{prev}\t{sent}")
            prev = sent
