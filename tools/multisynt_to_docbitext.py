import argparse
import gzip
import re
import json
import string
import sys

from langcodes import *
from loomchild.segmenter import LoomchildSegmenter


parser = argparse.ArgumentParser(description='merge translated documents back into jsonl')
parser.add_argument('-j', '--jsonl-file', help='original file in jsonl', type=str)
parser.add_argument('-s', '--source-language-file', help='source language file', type=str)
parser.add_argument('-t', '--target-language-file', help='target language file', type=str)
parser.add_argument('-m', '--minimum-length', help='minimal length in characters', type=int, default=0)
parser.add_argument('-l', '--length', help='requested approximate segment-length in characters', type=int, default=256)
args = parser.parse_args()

min_len = args.minimum_length
max_len = args.length


with gzip.open(args.jsonl_file,'rt', encoding='utf-8', errors='replace') as j:
    with gzip.open(args.source_language_file,'rt', encoding='utf-8', errors='replace') as s:
        with gzip.open(args.target_language_file,'rt', encoding='utf-8', errors='replace') as t:

            for line in j:
                document = json.loads(line)
                doc_segs = document['text'].splitlines()
 
                source_text = s.readline()
                target_text = t.readline()
                
                doc_id = 0;
                doc_text = doc_segs[doc_id]
                doc_nospace = re.sub(r"\s+", "", doc_text, flags=re.UNICODE)
                source_nospace = re.sub(r"\s+", "", source_text, flags=re.UNICODE)
                
                while source_nospace.startswith(doc_nospace) or doc_nospace.startswith(source_nospace):
                    
                    if doc_nospace == source_nospace:                        
                        src = source_text.rstrip().replace("\n",'\\n').replace("\t",'\\t')
                        trg = target_text.rstrip().replace("\n",'\\n').replace("\t",'\\t')

                        doc_id += 1
                        if doc_id >= len(doc_segs):
                            print(f"{src}\t{trg}")
                            break
                        
                        next_doc = doc_segs[doc_id]
                        if not next_doc: continue
                        next_src = s.readline()
                        next_trg = t.readline()

                        if ( len(src) >= min_len and len(src) <= max_len and (len(next_src) + len(source_text) > max_len) ) or (len(src) > max_len):
                            print(f"{src}\t{trg}")
                            source_text = next_src
                            target_text = next_trg
                            doc_text = next_doc
                        else:
                            source_text += next_src
                            target_text += next_trg
                            doc_text += next_doc

                        doc_nospace = re.sub(r"\s+", "", doc_text, flags=re.UNICODE)
                        source_nospace = re.sub(r"\s+", "", source_text, flags=re.UNICODE)
                            
                    elif source_nospace.startswith(doc_nospace):
                        doc_id += 1
                        if doc_id >= len(doc_segs): break
                        doc_text += doc_segs[doc_id]
                        doc_nospace = re.sub(r"\s+", "", doc_text, flags=re.UNICODE)
                    elif doc_nospace.startswith(source_nospace):
                        source_text += s.readline()
                        target_text += t.readline()
                        source_nospace = re.sub(r"\s+", "", source_text, flags=re.UNICODE)

                if source_nospace != 'END_OF_DOCUMENT':
                    source_text = s.readline()
                    target_text = t.readline()
                    source_nospace = re.sub(r"\s+", "", source_text, flags=re.UNICODE)
                
                print(f"END_OF_DOCUMENT\tEND_OF_DOCUMENT")
                if source_nospace != 'END_OF_DOCUMENT':
                    print(f"went beyond document boundary - this is bad!", file=sys.stderr)
                            
