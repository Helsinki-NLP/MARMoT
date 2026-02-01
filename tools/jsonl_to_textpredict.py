

import argparse
import gzip
import re
import json
import string
import sys

from loomchild.segmenter import LoomchildSegmenter
# from mosestokenizer import MosesSentenceSplitter


parser = argparse.ArgumentParser(description='fetch fineweb data and prepare for translation')
parser.add_argument('-i', '--input-file', help='input-file', type=str,
                    default='/scratch/project_462000963/datasets/HuggingFaceFW/fineweb-edu/350BT/fineweb-edu_350BT_00000.jsonl.gz')
parser.add_argument('-l', '--lang', help='document languages (default=en)', type=str, default='en')
parser.add_argument('-m', '--max-line-length', help='line length threshold in characters (default=256)', type=int, default=256)
parser.add_argument('-M', '--max-sentence-length', help='sentence length threshold in characters (default=1024)', type=int, default=1024)
parser.add_argument('-s', '--segment-into-sentences', help='split documents into sentences', action='store_true')
parser.add_argument('-S', '--source-file', help='source-file', type=str,default='source.txt.gz')
parser.add_argument('-T', '--target-file', help='target-file', type=str,default='target.txt.gz')
args = parser.parse_args()


## language (for sentence segmenter)
lang = args.lang


## segmenter for splitting into sentences
segmenter = LoomchildSegmenter(lang)
# moses_segmenter = MosesSentenceSplitter(lang)


## activate sentence splitter on all strings
sentsplit = args.segment_into_sentences

## max line length
max_line_length = args.max_line_length
max_sent_length = args.max_sentence_length
            


def convert_file(i,S,T):

    last_line = ''
    
    for line in i:
        
        try:
            document = json.loads(line)
        except:
            print(f"problem parsing {line}", file=sys.stderr)
            continue
                    
        ## a little trick to remove some newlines in the middle of a sentence
        ## TODO: does this break things more than it actually helps?
        text = re.sub(r"([A-Za-z,;])\n([a-z])", r"\1 \2", document['text'])

        ## split into sentences if needed
        if sentsplit:
            lines = segmenter.get_document_segmentation(text)
        else:
            lines = text.splitlines()
                

        ## process each line and split if necessary
        for line in lines:

            line = line.strip()
            if not line:
                continue

            ## no splitting necessary: just print the line
            if len(line) <= max_line_length:
                if last_line:
                    S.write(last_line + "\n")
                    T.write(line + "\n")
                last_line=line
                    
            ## otherwise: split into smaller segments
            else:

                ## split into sentences
                segments = segmenter.get_segmentation(line)
                seg = ''

                ## foreach sentence: check whether it is also too long (max_sent_length)
                ## if yes: split on punctuations                    
                for s in segments:
                    if len(s) > max_sent_length:
                        parts = re.findall(r'[^\s]+[^.?!,;:]+.?', s + ' ')
                    else:
                        parts = [s]

                    ## now merge segments again until we exceed the maximum length
                    ## once we are longer: print the segment and a newline
                    for p in parts:
                        p = p.strip()
                        if p:
                            if seg and (len(seg) + len(p) > max_line_length):
                                if last_line:
                                    S.write(last_line + "\n")
                                    T.write(seg + "\n")
                                last_line=seg
                                seg = ''
                            if seg:
                                seg += ' ' + p
                            else:
                                seg = p

                ## print the remaining segment if there is still something
                if seg:
                    if last_line:
                        S.write(last_line + "\n")
                        T.write(seg + "\n")
                    last_line=seg                        

        last_line=''
        # print("END_OF_DOCUMENT")




#######################################################################

with gzip.open(args.source_file, 'wt', encoding='utf-8') as S:
    with gzip.open(args.target_file, 'wt', encoding='utf-8') as T:
        with gzip.open(args.input_file, 'rt', encoding='utf-8') as i:
            convert_file(i,S,T)
