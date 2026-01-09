

.PHONY: all
all: devtest

devtest:
	wget -q -O flores200.tar.gz https://tinyurl.com/flores200dataset
	tar -xzf flores200.tar.gz
	mv flores200_dataset/* .
	rm flores200.tar.gz
	rmdir flores200_dataset
