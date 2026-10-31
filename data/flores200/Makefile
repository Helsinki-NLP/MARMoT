

.PHONY: all
all: devtest
	${MAKE} links

devtest:
	wget -q -O flores200.tar.gz https://tinyurl.com/flores200dataset
	tar -xzf flores200.tar.gz
	mv flores200_dataset/* .
	rm flores200.tar.gz
	rmdir flores200_dataset


.PHONY: links
links:
	for d in dev devtest; do \
	  cd $$d; \
	  ln -s lvs_Latn.$$d lav_Latn.$$d; \
	  ln -s als_Latn.$$d sqi_Latn.$$d; \
	  ln -s zsm_Latn.$$d msa_Latn.$$d; \
	  ln -s arb_Arab.$$d ara_Arab.$$d; \
	  ln -s arb_Latn.$$d ara_Latn.$$d; \
	  ln -s pes_Arab.$$d fas_Arab.$$d; \
	  ln -s kmr_Latn.$$d kur_Latn.$$d; \
	  ln -s ckb_Arab.$$d kur_Arab.$$d; \
	  cd ..; \
	done


## for FLORES++ we would also need:
#
#	  ln -s cmn_Hans.$$d zho_Hans.$$d
#	  ln -s cmn_Hant.$$d zho_Hant.$$d
