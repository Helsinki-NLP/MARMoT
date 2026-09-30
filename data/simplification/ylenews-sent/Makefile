

all: 	train/ylenews-fi-2014-2020-selko-par-sent.fin1.gz \
	train/ylenews-fi-2014-2020-selko-par-sent.fin2.gz \
	test/ylenews-fi-2014-2020-selko-par-sent.fin1.gz \
	test/ylenews-fi-2014-2020-selko-par-sent.fin2.gz


TRAIN_CSV := $(sort $(wildcard ylenews-fi-2014-2020-selko-par-sent-src/CSV/*.csv))
TRAIN_TSV := $(patsubst %.csv,%.tsv,$(TRAIN_CSV))


$(TRAIN_TSV): %.tsv: %.csv
	python3 csv2tsv.py $< > $@


train/ylenews-fi-2014-2020-selko-par-sent.fin1.gz: $(TRAIN_TSV)
	mkdir -p $(dir $@)
	find ylenews-fi-2014-2020-selko-par-sent-src/CSV -name '*.tsv' \
	| sort | xargs cat | egrep -v "^\s" | egrep -v "\s$$" | cut -f1 | gzip -c > $@

train/ylenews-fi-2014-2020-selko-par-sent.fin2.gz: $(TRAIN_TSV)
	mkdir -p $(dir $@)
	find ylenews-fi-2014-2020-selko-par-sent-src/CSV -name '*.tsv' \
	| sort | xargs cat | egrep -v "^\s" | egrep -v "\s$$" | cut -f2 | gzip -c > $@



TEST_CSV := $(sort $(wildcard ylenews-fi-2014-2020-selko-par-sent-src/golden_sentence_alignments_TEXT/*.csv))
TEST_TSV := $(patsubst %.csv,%.tsv,$(TEST_CSV))


$(TEST_TSV): %.tsv: %.csv
	python3 test_csv2tsv.py $< > $@

test/ylenews-fi-2014-2020-selko-par-sent.fin1.gz: $(TEST_TSV)
	mkdir -p $(dir $@)
	find ylenews-fi-2014-2020-selko-par-sent-src/golden_sentence_alignments_TEXT -name '*.tsv' \
	| sort | xargs cat | egrep -v "^\s" | egrep -v "\s$$" | cut -f1 | gzip -c > $@

test/ylenews-fi-2014-2020-selko-par-sent.fin2.gz: $(TEST_TSV)
	mkdir -p $(dir $@)
	find ylenews-fi-2014-2020-selko-par-sent-src/golden_sentence_alignments_TEXT -name '*.tsv' \
	| sort | xargs cat | egrep -v "^\s" | egrep -v "\s$$" | cut -f2 | gzip -c > $@
