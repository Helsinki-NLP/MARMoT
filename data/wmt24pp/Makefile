


LANGPAIRS := 	en-ar_EG en-ar_SA en-bg_BG en-bn_IN en-ca_ES en-cs_CZ en-da_DK en-de_DE \
		en-el_GR en-es_MX en-et_EE en-fa_IR en-fi_FI en-fil_PH en-fr_CA en-fr_FR \
		en-gu_IN en-he_IL en-hi_IN en-hr_HR en-hu_HU en-id_ID en-is_IS en-it_IT \
		en-ja_JP en-kn_IN en-ko_KR en-lt_LT en-lv_LV en-ml_IN en-mr_IN en-nl_NL \
		en-no_NO en-pa_IN en-pl_PL en-pt_BR en-pt_PT en-ro_RO en-ru_RU en-sk_SK \
		en-sl_SI en-sr_RS en-sv_SE en-sw_KE en-sw_TZ en-ta_IN en-te_IN en-th_TH \
		en-tr_TR en-uk_UA en-ur_PK en-vi_VN en-zh_CN en-zh_TW en-zu_ZA

LANGPAIR ?= ${firstword ${LANGPAIRS}}


SRC  := $(firstword $(subst -, ,${LANGPAIR}))
TRG  := $(lastword $(subst -, ,${LANGPAIR}))

SRC2 := $(firstword $(subst _, ,${SRC}))
TRG2 := $(firstword $(subst _, ,${TRG}))

SRC3 := $(shell iso639 -3 -n ${SRC})
TRG3 := $(shell iso639 -3 -n ${TRG})



.PHONY: all
all: ${LANGPAIRS}

.PHONY: ${LANGPAIRS}
${LANGPAIRS}:
	${MAKE} LANGPAIR=$@ extract

.PHONY: extract
extract: wmt24pp/${TRG}.${TRG3}.gz

wmt24pp/${TRG}.${TRG3}.gz: ${SRC}-${TRG}.jsonl
	mkdir -p $(dir $@)
	python ../../tools/wmt24_to_tsv.py < $< > $@.tsv
	if [ ! -e ${SRC}.${SRC3}.gz ]; then  \
	  cut -f1 $@.tsv | gzip -c > wmt24pp/${SRC}.${SRC3}.gz; \
	fi
	cut -f2 $@.tsv | gzip -c > $@
	rm -f $@.tsv


# .PHONY: extract
# extract: wmt24pp/${SRC3}-${TRG3}.${SRC3}.gz

# wmt24pp/${SRC3}-${TRG3}.${SRC3}.gz: ${SRC}-${TRG}.jsonl
# 	mkdir -p $(dir $@)
# 	python ../../tools/wmt24_to_tsv.py < $< > $@.tsv
# 	cut -f1 $@.tsv | gzip -c > $@
# 	cut -f1 $@.tsv | gzip -c > $(@:.${SRC3}.gz=.${TRG3}.gz)
# 	rm -f $@.tsv









.PHONY: predict
predict: next_sent_predict/wmt24pp_${SRC3}-${TRG3}.${SRC3}.in.gz \
	next_sent_predict/wmt24pp_${SRC3}-${TRG3}.${TRG3}.in.gz

${SRC}-${TRG}.jsonl:
	wget -q -O $@ https://huggingface.co/datasets/google/wmt24pp/raw/main/$@

next_sent_predict/wmt24pp_${SRC3}-${TRG3}.${SRC3}.in.gz: ${SRC}-${TRG}.jsonl
	mkdir -p $(dir $@)
	python3 ../../tools/wmt24_to_predict.py -l ${SRC2} -i $< -f source > $@.tsv
	cut -f1 $@.tsv | gzip -c > $@
	cut -f2 $@.tsv | gzip -c > $(@:.in.gz=.out.gz)
	rm -f $@.tsv

next_sent_predict/wmt24pp_${SRC3}-${TRG3}.${TRG3}.in.gz: ${SRC}-${TRG}.jsonl
	mkdir -p $(dir $@)
	python3 ../../tools/wmt24_to_predict.py -l ${TRG2} -i $< -f target > $@.tsv
	cut -f1 $@.tsv | gzip -c > $@
	cut -f2 $@.tsv | gzip -c > $(@:.in.gz=.out.gz)
	rm -f $@.tsv
