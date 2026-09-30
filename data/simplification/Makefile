

all: ylenews/train/ylenews.fin1.gz ylenews/train/ylenews.fin2.gz

ylenews/train/ylenews.fin1.gz:
	mkdir -p $(dir $@)
	zcat ylenews-sent/train/*.fin1.gz  ylenews-par/train/*.fin1.gz | gzip -c > $@

ylenews/train/ylenews.fin2.gz:
	mkdir -p $(dir $@)
	zcat ylenews-sent/train/*.fin2.gz  ylenews-par/train/*.fin2.gz | gzip -c > $@
