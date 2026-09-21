

import argparse
import json
import sys
import io
import signal

from loomchild.segmenter import LoomchildSegmenter

import zstandard as zstd
import numpy as np

# import sentalign_banded as sentalign
# import sentalign_fast as sentalign
# import sentalign as sentalign



def read_zst_lines(path):
    with open(path, "rb") as fh:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(fh) as reader:
            text_stream = io.TextIOWrapper(reader, encoding="utf-8")
            for line in text_stream:
                yield line.rstrip("\n")


# Alignment types: (da, db, prior)
ALIGN_TYPES = np.array([
    (1, 1, 0.878),
    (2, 1, 0.05),
    (1, 2, 0.05),
    (3, 1, 0.01),
    (1, 3, 0.01),
    (0, 1, 0.001),
    (1, 0, 0.001),
], dtype=float)


## parameters for aligning paragraphs to lines
## does not add to 1 at the moment (who cares?)
PAR_ALIGN_TYPES = np.array([
    (1, 0, 0.00001),
    (0, 1, 0.00001),
    (1, 1, 0.8),
    (2, 1, 0.01),
    (1, 2, 0.01),
    (3, 1, 0.005),
    (1, 3, 0.005),
    (1, 4, 0.001),
    (4, 1, 0.001),
    (1, 5, 0.0005),
    (5, 1, 0.0005),
    (1, 6, 0.0001),
    (6, 1, 0.0001),
], dtype=float)


## parameters for aligning paragraphs to paragraphs
## (focusing heavily on one-to-one alignments)
## does not add to 1 at the moment (who cares?)
STRONG_ONE2ONE_ALIGN_TYPES = np.array([
    (1, 1, 0.9),
    (2, 1, 0.000001),
    (1, 2, 0.000001),
    (3, 1, 0.00000001),
    (1, 3, 0.00000001),
    (0, 1, 0.0000000001),
    (1, 0, 0.0000000001)
], dtype=float)


## aligning paragraphs to lines/sentences
## we want to keep paragraph segmentation in the source
## --> only 1:x alignments are allowed
## --> 1:0 alignments are not preferred
ONE_TO_X_ALIGN_TYPES = np.array([
    (1, 0, 0.001),
    (1, 1, 0.1),
    (1, 2, 0.1),
    (1, 3, 0.1),
    (1, 4, 0.1),
    (1, 5, 0.1),
    (1, 6, 0.1),
    (1, 7, 0.1),
    (1, 8, 0.1),
    (1, 9, 0.1),
    (1, 10, 0.1),
], dtype=float)

VARIANCE = 6.8

## this additional factor increases varians with length (source + target string)
## motivation: variance get's bigger with larger segments making it less costly
##             to align longer segments that do not match that well in terms of length
LENGTH_VAR_FACTOR = 0.01

def sentence_lengths(sentences):
    return np.array([len(s) for s in sentences], dtype=np.float64)

def prefix_sums(lengths):
    """Prefix sums for O(1) segment length queries"""
    return np.concatenate(([0.0], np.cumsum(lengths)))

def segment_sum(prefix, i, j):
    return prefix[j] - prefix[i]

def estimate_mean_ratio(len_a, len_b):
    return len_b.sum() / max(len_a.sum(), 1.0)

def alignment_cost(sum_a, sum_b, mean_ratio):
    expected_b = sum_a * mean_ratio
    delta = sum_b - expected_b
    var = VARIANCE + LENGTH_VAR_FACTOR * (sum_a + sum_b)
    return (delta ** 2) / (2 * var)
    # return (delta ** 2) / (2 * VARIANCE)

def align(a, b, aligntypes=ALIGN_TYPES):
    n, m = len(a), len(b)

    len_a = sentence_lengths(a)
    len_b = sentence_lengths(b)

    prefix_a = prefix_sums(len_a)
    prefix_b = prefix_sums(len_b)

    mean_ratio = estimate_mean_ratio(len_a, len_b)

    # DP tables
    dp = np.full((n + 1, m + 1), np.inf)
    dp[0, 0] = 0.0

    back = [[None] * (m + 1) for _ in range(n + 1)]

    # Precompute log priors
    log_priors = -np.log(aligntypes[:, 2])

    for i in range(n + 1):
        for j in range(m + 1):
            base = dp[i, j]
            if not np.isfinite(base):
                continue

            # Vectorized over alignment types
            for k in range(len(aligntypes)):
                da = int(aligntypes[k, 0])
                db = int(aligntypes[k, 1])

                ni, nj = i + da, j + db
                if ni > n or nj > m:
                    continue

                sum_a = prefix_a[ni] - prefix_a[i]
                sum_b = prefix_b[nj] - prefix_b[j]

                cost = alignment_cost(sum_a, sum_b, mean_ratio)
                total_cost = base + cost + log_priors[k]

                if total_cost < dp[ni, nj]:
                    dp[ni, nj] = total_cost
                    back[ni][nj] = (i, j, da, db)

    # Backtrack
    alignments = []
    i, j = n, m

    while (i, j) != (0, 0):
        prev = back[i][j]
        if prev is None:
            break

        pi, pj, da, db = prev
        alignments.append((a[pi:i], b[pj:j]))
        i, j = pi, pj

    alignments.reverse()
    return alignments


def print_aligned_lines(srcseg, trglines):
    start = 0
    count = 0
    for srctxt in srcseg:
        srclen = len(list(filter(None,srctxt.splitlines())))
        stop = start+srclen
        # print(f"sentences from {start} to {stop}", file=sys.stderr)
        trgalg = trglines[start:stop]
        start = stop
        srcstr = srctxt.replace("\n",'\\n')
        trgstr = '\\n'.join(trgalg)
        if srcstr:
            print(f"{srcstr}\t{trgstr}")
            count += 1
    return count

        
def timeout_handler(signum, frame):
    raise Exception('Warning: Action took too much time')


def align_sentences(srcdoc, trgdoc, srcSeg, trgSeg):

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(10)
    try:
        srcsent = srcSeg.get_document_segmentation(srcdoc)
        trgsent = trgSeg.get_document_segmentation(trgdoc)
    except:
        print(f"Warning: sentence splitter timeout", file=sys.stderr)
    signal.alarm(0)

    aligned = align(srcsent, trgsent, SENT_ALIGN_TYPES)
    count = 0
    for src, trg in aligned:
        srcstr = '\\n'.join(src)
        trgstr = '\\n'.join(trg)
        if srcstr:
            print(f"{srcstr}\t{trgstr}")
            count += 1
    return count

    


def align_paragraphs(srcseg, trgseg, trglines, segmenter):
    
    srcseglen = len(srcseg)
    trgseglen = len(trgseg)
    trglinelen = len(trglines)
    # print(f"need to fit: {srcseglen} - {trgseglen} / {trglinelen}", file=sys.stderr)

    ## if nr of target segments < nr of source segments: align target lines instead of target segments
    ## (only if nr of target lines is not more than double the nr of source segments)
    #if srcseglen/trgseglen > 0.9 and srcseglen/trgseglen < 1.1:
    #    segaligned = align(srcseg, trglines, STRONG_ONE2ONE_ALIGN_TYPES)
    if trgseglen < srcseglen and trglinelen > trgseglen and trglinelen < srcseglen*2:
        segaligned = align(srcseg, trglines, PAR_ALIGN_TYPES)
    else:                
        segaligned = align(srcseg, trgseg, STRONG_ONE2ONE_ALIGN_TYPES)

    ## run through all alignments
    ## if there are more than one source segment in an alignment: try to align lines or even sentences
    ## (this is because we want to keep one source segment per line in the output to make it a multiparallel corpus)
    
    count = 0
    signal.signal(signal.SIGALRM, timeout_handler)
    
    for src, trg in segaligned:
        srclen = len(src)

        if srclen==0:
            continue
        elif srclen == 1:
            srcstr = '\\n'.join(src).replace("\n",'\\n')
            trgstr = '\\n'.join(trg).replace("\n",'\\n')
            if srcstr:
                print(f"{srcstr}\t{trgstr}")
                count += 1
        else:
            trgstr = "\n".join(trg)
            trgsent = list(filter(None,trgstr.splitlines()))

            ## fewer lines than source segments: split target language string into sentences
            if len(trgsent) < srclen:
                signal.alarm(10)
                try:
                    trgsent = segmenter.get_document_segmentation(trgstr)
                except:
                    print(f"Warning: sentence splitter timeout", file=sys.stderr)
                signal.alarm(0)

                ## still fewer segments in target language than source language?
                ## print a warning and try the best with aligning segments
                # if len(trgsent) < srclen:
                #    print(f"Warning: cannot properly split {trgstr} into segments to align to {srclen} source segments", file=sys.stderr)

            ## align target language segments to each single source language segment
            ## we only allow 1:x alignments because we want to keep the same number of lines
            ## for each target language (assume that source segments are proper paragraphs that can be aligned)
            aligned = align(src, trgsent, ONE_TO_X_ALIGN_TYPES)

            ## no alignments found?
            ## just print all source language paragraphs and leave the target side blank
            ## TODO: is that a good ide?
            if (len(aligned) == 0):
                print(f"Warning! No alignments found for {srclen} segments", file=sys.stderr)
                for srctxt in src:
                    srcstr = srctxt.replace("\n",'\\n')
                    if srcstr:
                        print(f"{srcstr}\t")
                        count += 1

            ## if we have fewer alignments than source language paragraphs
            ## then this is a serious problem! What do we do?
            ## same as above: print source language paragraphs and leave target blank
            elif (len(aligned) < srclen):
                alglen = len(aligned)
                print(f"Warning! Not all segments are aligned ({alglen} != {srclen})", file=sys.stderr)
                for srctxt in src:
                    srcstr = srctxt.replace("\n",'\\n')
                    if srcstr:
                        print(f"{srcstr}\t")
                        count += 1

            ## print all aligned segments
            else:
                for srctxt, trgtxt in aligned:
                    srcstr = '\\n'.join(srctxt).replace("\n",'\\n')
                    trgstr = '\\n'.join(trgtxt).replace("\n",'\\n')
                    if srcstr:
                        print(f"{srcstr}\t{trgstr}")
                        count += 1
            
    if count < len(srcseg):
        print(f"Warning! Not all segments are printed ({count} != {srclen})", file=sys.stderr)
    return count



def extract_bitext(source_file, target_file, target_lang):

    incount = 0
    outcount = 0
    
    trgSegmenter = LoomchildSegmenter(target_lang)
    for srcline, trgline in zip(read_zst_lines(source_file),
                                read_zst_lines(target_file)):
        try:
            srcdoc = json.loads(srcline)
            srcseg = [s for s in srcdoc['text'].split("\n\n") if s]
            incount += len(srcseg)
        except:
            print(f"problem parsing {srcline}", file=sys.stderr)
            continue

        try:
            trgdoc = json.loads(trgline)
        except:
            print(f"problem parsing {trgline}", file=sys.stderr)
            ## print source segments anyway to get the same number of lines
            ## as for other language pairs
            for srctxt in srcseg:
                srcstr = srctxt.replace("\n",'\\n')
                if srcstr:
                    print(f"{srcstr}\t")
                    outcount += 1
            print(f"END_OF_DOCUMENT\tEND_OF_DOCUMENT")
            continue

        if 'I was very much worried about this problem' in srcdoc['text']:
            print('')

        trgseg = [s for s in trgdoc['text'].split("\n\n") if s]
        trglines = [s for s in trgdoc['text'].splitlines() if s]
        outcount += align_paragraphs(srcseg, trgseg, trglines, trgSegmenter)
        print(f"END_OF_DOCUMENT\tEND_OF_DOCUMENT")
        
    print(f"=============\nextracted: {outcount}/{incount} segments\n==========================", file=sys.stderr)
    return outcount


                



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='extract parallel segments from parallel MultiSynt')
    parser.add_argument('-s', '--source-file', help='source language file', type=str)
    parser.add_argument('-t', '--target-file', help='target language file', type=str)
    parser.add_argument('-l', '--lang', help='target language (default=fi)', type=str, default='fi')
    args = parser.parse_args()

    count = extract_bitext(args.source_file, args.target_file, args.lang)

