
ylenews-par: 	train/ylenews-fi-2014-2018-selko-par.fin1.gz \
		train/ylenews-fi-2014-2018-selko-par.fin2.gz

ylenews-fi-2014-2018-selko-par-src.tsv: ylenews-fi-2014-2018-selko-par-src.csv
	python3 csv2tsv.py $< > $@


train/ylenews-fi-2014-2018-selko-par.fin1.gz: ylenews-fi-2014-2018-selko-par-src.tsv
	mkdir -p $(dir $@)
	cut -f1 < $< | gzip -c > $@

train/ylenews-fi-2014-2018-selko-par.fin2.gz: ylenews-fi-2014-2018-selko-par-src.tsv
	mkdir -p $(dir $@)
	cut -f2 < $< | gzip -c > $@

