## doc-level MT trained on MultiSynt data
## Encoder: 3 layers shared across language groups + 3 layers completely shared
## Decoder: 6 language-specific layers



include ../../../make/env.mk


## model architecture

ENCODER            := "{langgroup}","all"
ENCODER_LAYERS     := 2,4
DECODER_LAYERS     := 3
MODEL_DIMENSION    := 768
TRF_HEADS          := 4



## data directories

TRANSLATE_TRAIN_DOC  := multisynt/train/len1024
TRANSLATE_TRAIN_SENT := sentmt
DEVDATA              := flores200/dev


USE_DATASIZE_AS_TASK_WEIGHT := 1


## docmt languages and tasks

LANGUAGES := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr

## English-centric docmt translation tasks

DOCMT_PIVOT_LANGS := eng
DOCMT_TASKS       := $(sort $(foreach p,${DOCMT_PIVOT_LANGS},$(foreach l,$(filter-out $p,${LANGUAGES}),$l-$p $p-$l)))
DOCMT_TASK_IDS    := $(addprefix docmt_,${DOCMT_TASKS})
DOCMT_TRAINDATA   := $(foreach l,${DOCMT_TASKS},${TRANSLATE_TRAIN_DOC})



## OPUS sentence-level MT training data (with more that 10 million training exampels)

SENTMT_LANGPAIRS := afr-eng ara-bos ara-bul ara-ces ara-dan ara-deu ara-ell ara-eng ara-eng_ze ara-est ara-fas ara-fin ara-fra ara-heb ara-hrv ara-hun ara-ind ara-ita ara-jpn ara-kor ara-msa ara-nld ara-nor ara-pol ara-por ara-por_BR ara-por_MZ ara-ron ara-rus ara-slk ara-slv ara-spa ara-spa_419 ara-spa_ES ara-srp ara-swe ara-tha ara-tur ara-vie aze_Latn-eng bel-eng bel-rus ben-eng bos-ara bos-bul bos-ces bos-dan bos-deu bos-ell bos-eng bos-eng_ze bos-fin bos-fra bos-heb bos-hrv bos-hun bos-ita bos-nld bos-pol bos-por bos-por_BR bos-por_MZ bos-ron bos-spa bos-spa_419 bos-spa_ES bos-srp bos-swe bos-tur bos_Latn-eng bul-ara bul-bos bul-ces bul-dan bul-deu bul-ell bul-eng bul-eng_ze bul-est bul-fas bul-fin bul-fra bul-heb bul-hrv bul-hun bul-ind bul-ita bul-kor bul-nld bul-nor bul-pol bul-por bul-por_BR bul-por_MZ bul-ron bul-rus bul-slv bul-spa bul-spa_419 bul-spa_ES bul-srp bul-swe bul-tha bul-tur bul-ukr bul-vie bul-zho_Hans cat-eng cat-fra cat-ita cat-por cat-spa ceb-eng ces-ara ces-bos ces-bul ces-dan ces-deu ces-ell ces-eng ces-eng_ze ces-est ces-fas ces-fin ces-fra ces-heb ces-hrv ces-hun ces-ind ces-ita ces-kor ces-nld ces-nor ces-pol ces-por ces-por_BR ces-por_MZ ces-ron ces-rus ces-slv ces-spa ces-spa_419 ces-spa_ES ces-srp ces-swe ces-tha ces-tur ces-ukr ces-vie cym-eng dan-ara dan-bos dan-bul dan-ces dan-deu dan-ell dan-eng dan-eng_ze dan-est dan-fas dan-fin dan-fra dan-heb dan-hrv dan-hun dan-ind dan-ita dan-kor dan-nld dan-nor dan-pol dan-por dan-por_BR dan-por_MZ dan-ron dan-rus dan-slv dan-spa dan-spa_419 dan-spa_ES dan-srp dan-swe dan-tha dan-tur dan-vie deu-ara deu-bos deu-bul deu-ces deu-dan deu-ell deu-eng deu-eng_ze deu-est deu-fas deu-fin deu-fra deu-hbs_Latn deu-heb deu-hrv deu-hun deu-ind deu-isl deu-ita deu-jpn deu-kor deu-lav deu-lit deu-msa deu-msa_Latn deu-nld deu-nor deu-pol deu-por deu-por_BR deu-por_MZ deu-ron deu-rus deu-slv deu-spa deu-spa_419 deu-spa_ES deu-srp deu-srp_Latn deu-swe deu-tha deu-tur deu-ukr deu-vie deu-zho_Hans ell-ara ell-bos ell-bul ell-ces ell-dan ell-deu ell-eng ell-eng_ze ell-est ell-fas ell-fin ell-fra ell-heb ell-hrv ell-hun ell-ind ell-ita ell-kor ell-msa ell-nld ell-nor ell-pol ell-por ell-por_BR ell-por_MZ ell-ron ell-rus ell-slk ell-slv ell-spa ell-spa_419 ell-spa_ES ell-srp ell-swe ell-tha ell-tur ell-vie eng-afr eng-ara eng-aze_Latn eng-bel eng-ben eng-bos eng-bos_Latn eng-bul eng-cat eng-ceb eng-ces eng-cym eng-dan eng-deu eng-ell eng-eng eng-epo eng-est eng-eus eng-fas eng-fin eng-fra eng-gle eng-glg eng-hbs_Latn eng-heb eng-hin eng-hrv eng-hun eng-hye eng-ind eng-isl eng-ita eng-jav eng-jpn eng-kat eng-kaz_Cyrl eng-kor eng-lav eng-lit eng-ltz eng-mal eng-mar eng-mkd eng-mlt eng-mon eng-msa eng-msa_Latn eng-mya eng-nld eng-nob eng-nor eng-pol eng-por eng-por_BR eng-por_MZ eng-ron eng-rus eng-slk eng-slv eng-spa eng-spa_419 eng-spa_ES eng-sqi eng-srp eng-srp_Cyrl eng-srp_Latn eng-swa eng-swe eng-tam eng-tat eng-tel eng-tgl_Latn eng-tha eng-tur eng-ukr eng-urd eng-uzb_Latn eng-vie eng-zho_Hans eng-zho_Hant eng_ze-ara eng_ze-bos eng_ze-bul eng_ze-ces eng_ze-dan eng_ze-deu eng_ze-ell eng_ze-est eng_ze-fas eng_ze-fin eng_ze-fra eng_ze-heb eng_ze-hrv eng_ze-hun eng_ze-ind eng_ze-ita eng_ze-kor eng_ze-msa eng_ze-nld eng_ze-nor eng_ze-pol eng_ze-por eng_ze-por_BR eng_ze-ron eng_ze-rus eng_ze-slk eng_ze-slv eng_ze-spa eng_ze-spa_419 eng_ze-spa_ES eng_ze-srp eng_ze-swe eng_ze-tha eng_ze-tur eng_ze-ukr eng_ze-vie epo-eng epo-fra est-ara est-bul est-ces est-dan est-deu est-ell est-eng est-eng_ze est-fas est-fin est-fra est-heb est-hrv est-hun est-ind est-ita est-nld est-nor est-pol est-por est-por_BR est-por_MZ est-ron est-rus est-slv est-spa est-spa_419 est-spa_ES est-srp est-swe est-tur est-vie eus-eng eus-spa fas-ara fas-bul fas-ces fas-dan fas-deu fas-ell fas-eng fas-eng_ze fas-est fas-fin fas-fra fas-heb fas-hrv fas-hun fas-ind fas-ita fas-kor fas-msa fas-nld fas-nor fas-pol fas-por fas-por_BR fas-por_MZ fas-ron fas-rus fas-slv fas-spa fas-spa_419 fas-spa_ES fas-srp fas-swe fas-tha fas-tur fas-vie fin-ara fin-bos fin-bul fin-ces fin-dan fin-deu fin-ell fin-eng fin-eng_ze fin-est fin-fas fin-fra fin-heb fin-hrv fin-hun fin-ind fin-ita fin-jpn fin-kor fin-nld fin-nor fin-pol fin-por fin-por_BR fin-por_MZ fin-ron fin-rus fin-slv fin-spa fin-spa_419 fin-spa_ES fin-srp fin-swe fin-tha fin-tur fin-vie fin-zho_Hans fra-ara fra-bos fra-bul fra-cat fra-ces fra-dan fra-deu fra-ell fra-eng fra-eng_ze fra-epo fra-est fra-fas fra-fin fra-hbs_Latn fra-heb fra-hrv fra-hun fra-ind fra-ita fra-jpn fra-kor fra-msa fra-msa_Latn fra-nld fra-nor fra-pol fra-por fra-por_BR fra-por_MZ fra-ron fra-rus fra-slv fra-spa fra-spa_419 fra-spa_ES fra-srp fra-srp_Latn fra-swe fra-tha fra-tur fra-ukr fra-vie fra-zho_Hans gle-eng glg-eng glg-por glg-spa hbs_Latn-deu hbs_Latn-eng hbs_Latn-fra hbs_Latn-ita hbs_Latn-nor hbs_Latn-pol hbs_Latn-rus hbs_Latn-spa hbs_Latn-tur hbs_Latn-zho_Hans heb-ara heb-bos heb-bul heb-ces heb-dan heb-deu heb-ell heb-eng heb-eng_ze heb-est heb-fas heb-fin heb-fra heb-hrv heb-hun heb-ind heb-ita heb-jpn heb-kor heb-nld heb-nor heb-pol heb-por heb-por_BR heb-por_MZ heb-ron heb-rus heb-slv heb-spa heb-spa_419 heb-spa_ES heb-srp heb-swe heb-tha heb-tur heb-ukr heb-vie heb-zho_Hans hin-eng hrv-ara hrv-bos hrv-bul hrv-ces hrv-dan hrv-deu hrv-ell hrv-eng hrv-eng_ze hrv-est hrv-fas hrv-fin hrv-fra hrv-heb hrv-hun hrv-ind hrv-ita hrv-kor hrv-nld hrv-nor hrv-pol hrv-por hrv-por_BR hrv-por_MZ hrv-ron hrv-rus hrv-slv hrv-spa hrv-spa_419 hrv-spa_ES hrv-srp hrv-swe hrv-tha hrv-tur hrv-ukr hrv-vie hun-ara hun-bos hun-bul hun-ces hun-dan hun-deu hun-ell hun-eng hun-eng_ze hun-est hun-fas hun-fin hun-fra hun-heb hun-hrv hun-ind hun-ita hun-jpn hun-kor hun-nld hun-nor hun-pol hun-por hun-por_BR hun-por_MZ hun-ron hun-rus hun-slk hun-slv hun-spa hun-spa_419 hun-spa_ES hun-srp hun-swe hun-tha hun-tur hun-ukr hun-vie hun-zho_Hans hye-eng ind-ara ind-bul ind-ces ind-dan ind-deu ind-ell ind-eng ind-eng_ze ind-est ind-fas ind-fin ind-fra ind-heb ind-hrv ind-hun ind-ita ind-kor ind-msa ind-nld ind-nor ind-pol ind-por ind-por_BR ind-por_MZ ind-ron ind-rus ind-slv ind-spa ind-spa_419 ind-spa_ES ind-srp ind-swe ind-tha ind-tur ind-vie isl-deu isl-eng ita-ara ita-bos ita-bul ita-cat ita-ces ita-dan ita-deu ita-ell ita-eng ita-eng_ze ita-est ita-fas ita-fin ita-fra ita-hbs_Latn ita-heb ita-hrv ita-hun ita-ind ita-jpn ita-kor ita-lit ita-msa ita-msa_Latn ita-nld ita-nor ita-pol ita-por ita-por_BR ita-por_MZ ita-ron ita-rus ita-slv ita-spa ita-spa_419 ita-spa_ES ita-srp ita-swe ita-tha ita-tur ita-ukr ita-vie ita-zho_Hans jav-eng jpn-ara jpn-deu jpn-eng jpn-fin jpn-fra jpn-heb jpn-hun jpn-ita jpn-kor jpn-msa_Latn jpn-nld jpn-pol jpn-por jpn-rus jpn-spa jpn-swe jpn-tur jpn-zho_Hans kat-eng kaz_Cyrl-eng kor-ara kor-bul kor-ces kor-dan kor-deu kor-ell kor-eng kor-eng_ze kor-fas kor-fin kor-fra kor-heb kor-hrv kor-hun kor-ind kor-ita kor-jpn kor-nld kor-nor kor-pol kor-por kor-por_BR kor-por_MZ kor-ron kor-rus kor-spa kor-spa_419 kor-spa_ES kor-srp kor-swe kor-tha kor-tur kor-vie lav-deu lav-eng lav-rus lit-deu lit-eng lit-ita lit-pol lit-rus lit-spa lit-tur ltz-eng mal-eng mar-eng mkd-eng mlt-eng mon-eng msa-ara msa-deu msa-ell msa-eng msa-eng_ze msa-fas msa-fra msa-ind msa-ita msa-pol msa-por msa-por_BR msa-por_MZ msa-ron msa-spa msa-spa_419 msa-spa_ES msa-tur msa-vie msa_Latn-deu msa_Latn-eng msa_Latn-fra msa_Latn-ita msa_Latn-jpn msa_Latn-msa_Latn msa_Latn-spa msa_Latn-zho_Hans mya-eng nld-ara nld-bos nld-bul nld-ces nld-dan nld-deu nld-ell nld-eng nld-eng_ze nld-est nld-fas nld-fin nld-fra nld-heb nld-hrv nld-hun nld-ind nld-ita nld-jpn nld-kor nld-nor nld-pol nld-por nld-por_BR nld-por_MZ nld-ron nld-rus nld-slv nld-spa nld-spa_419 nld-spa_ES nld-srp nld-swe nld-tha nld-tur nld-ukr nld-vie nld-zho_Hans nob-eng nor-ara nor-bul nor-ces nor-dan nor-deu nor-ell nor-eng nor-eng_ze nor-est nor-fas nor-fin nor-fra nor-hbs_Latn nor-heb nor-hrv nor-hun nor-ind nor-ita nor-kor nor-nld nor-pol nor-por nor-por_BR nor-por_MZ nor-ron nor-rus nor-slv nor-spa nor-spa_419 nor-spa_ES nor-srp nor-swe nor-tha nor-tur nor-ukr nor-vie pol-ara pol-bos pol-bul pol-ces pol-dan pol-deu pol-ell pol-eng pol-eng_ze pol-est pol-fas pol-fin pol-fra pol-hbs_Latn pol-heb pol-hrv pol-hun pol-ind pol-ita pol-jpn pol-kor pol-lit pol-msa pol-nld pol-nor pol-por pol-por_BR pol-por_MZ pol-ron pol-rus pol-slk pol-slv pol-spa pol-spa_419 pol-spa_ES pol-srp pol-srp_Latn pol-swe pol-tha pol-tur pol-ukr pol-vie pol-zho_Hans por-ara por-bos por-bul por-cat por-ces por-dan por-deu por-ell por-eng por-eng_ze por-est por-fas por-fin por-fra por-glg por-heb por-hrv por-hun por-ind por-ita por-jpn por-kor por-msa por-nld por-nor por-pol por-por por-ron por-rus por-slv por-spa por-spa_419 por-spa_ES por-srp por-swe por-tha por-tur por-ukr por-vie por-zho_Hans por-zho_Hant por_BR-ara por_BR-bos por_BR-bul por_BR-ces por_BR-dan por_BR-deu por_BR-ell por_BR-eng por_BR-eng_ze por_BR-est por_BR-fas por_BR-fin por_BR-fra por_BR-heb por_BR-hrv por_BR-hun por_BR-ind por_BR-ita por_BR-kor por_BR-msa por_BR-nld por_BR-nor por_BR-pol por_BR-ron por_BR-rus por_BR-slv por_BR-spa por_BR-spa_419 por_BR-spa_ES por_BR-srp por_BR-swe por_BR-tha por_BR-tur por_BR-vie por_MZ-ara por_MZ-bos por_MZ-bul por_MZ-ces por_MZ-dan por_MZ-deu por_MZ-ell por_MZ-eng por_MZ-est por_MZ-fas por_MZ-fin por_MZ-fra por_MZ-heb por_MZ-hrv por_MZ-hun por_MZ-ind por_MZ-ita por_MZ-kor por_MZ-msa por_MZ-nld por_MZ-nor por_MZ-pol por_MZ-ron por_MZ-rus por_MZ-slv por_MZ-spa por_MZ-spa_419 por_MZ-srp por_MZ-swe por_MZ-tha por_MZ-tur por_MZ-vie ron-ara ron-bos ron-bul ron-ces ron-dan ron-deu ron-ell ron-eng ron-eng_ze ron-est ron-fas ron-fin ron-fra ron-heb ron-hrv ron-hun ron-ind ron-ita ron-kor ron-msa ron-nld ron-nor ron-pol ron-por ron-por_BR ron-por_MZ ron-rus ron-slk ron-slv ron-spa ron-spa_419 ron-spa_ES ron-srp ron-swe ron-tha ron-tur ron-vie rus-ara rus-bel rus-bul rus-ces rus-dan rus-deu rus-ell rus-eng rus-eng_ze rus-est rus-fas rus-fin rus-fra rus-hbs_Latn rus-heb rus-hrv rus-hun rus-ind rus-ita rus-jpn rus-kor rus-lav rus-lit rus-nld rus-nor rus-pol rus-por rus-por_BR rus-por_MZ rus-ron rus-slv rus-spa rus-spa_419 rus-spa_ES rus-srp rus-swe rus-tha rus-tur rus-ukr rus-vie rus-zho_Hans slk-ara slk-ell slk-eng slk-eng_ze slk-hun slk-pol slk-ron slk-spa slk-spa_419 slk-spa_ES slk-tur slv-ara slv-bul slv-ces slv-dan slv-deu slv-ell slv-eng slv-eng_ze slv-est slv-fas slv-fin slv-fra slv-heb slv-hrv slv-hun slv-ind slv-ita slv-nld slv-nor slv-pol slv-por slv-por_BR slv-por_MZ slv-ron slv-rus slv-spa slv-spa_419 slv-spa_ES slv-srp slv-swe slv-tur slv-ukr spa-ara spa-bos spa-bul spa-cat spa-ces spa-dan spa-deu spa-ell spa-eng spa-eng_ze spa-est spa-eus spa-fas spa-fin spa-fra spa-glg spa-hbs_Latn spa-heb spa-hrv spa-hun spa-ind spa-ita spa-jpn spa-kor spa-lit spa-msa spa-msa_Latn spa-nld spa-nor spa-pol spa-por spa-por_BR spa-por_MZ spa-ron spa-rus spa-slk spa-slv spa-srp spa-srp_Latn spa-swe spa-tha spa-tur spa-ukr spa-vie spa-zho_Hans spa_419-ara spa_419-bos spa_419-bul spa_419-ces spa_419-dan spa_419-deu spa_419-ell spa_419-eng spa_419-eng_ze spa_419-est spa_419-fas spa_419-fin spa_419-fra spa_419-heb spa_419-hrv spa_419-hun spa_419-ind spa_419-ita spa_419-kor spa_419-msa spa_419-nld spa_419-nor spa_419-pol spa_419-por spa_419-por_BR spa_419-por_MZ spa_419-ron spa_419-rus spa_419-slk spa_419-slv spa_419-srp spa_419-swe spa_419-tha spa_419-tur spa_419-vie spa_ES-ara spa_ES-bos spa_ES-bul spa_ES-ces spa_ES-dan spa_ES-deu spa_ES-ell spa_ES-eng spa_ES-eng_ze spa_ES-est spa_ES-fas spa_ES-fin spa_ES-fra spa_ES-heb spa_ES-hrv spa_ES-hun spa_ES-ind spa_ES-ita spa_ES-kor spa_ES-msa spa_ES-nld spa_ES-nor spa_ES-pol spa_ES-por spa_ES-por_BR spa_ES-ron spa_ES-rus spa_ES-slk spa_ES-slv spa_ES-srp spa_ES-swe spa_ES-tha spa_ES-tur spa_ES-vie sqi-eng srp-ara srp-bos srp-bul srp-ces srp-dan srp-deu srp-ell srp-eng srp-eng_ze srp-est srp-fas srp-fin srp-fra srp-heb srp-hrv srp-hun srp-ind srp-ita srp-kor srp-nld srp-nor srp-pol srp-por srp-por_BR srp-por_MZ srp-ron srp-rus srp-slv srp-spa srp-spa_419 srp-spa_ES srp-swe srp-tha srp-tur srp-vie srp_Cyrl-eng srp_Latn-deu srp_Latn-eng srp_Latn-fra srp_Latn-pol srp_Latn-spa srp_Latn-tur swa-eng swe-ara swe-bos swe-bul swe-ces swe-dan swe-deu swe-ell swe-eng swe-eng_ze swe-est swe-fas swe-fin swe-fra swe-heb swe-hrv swe-hun swe-ind swe-ita swe-jpn swe-kor swe-nld swe-nor swe-pol swe-por swe-por_BR swe-por_MZ swe-ron swe-rus swe-slv swe-spa swe-spa_419 swe-spa_ES swe-srp swe-tha swe-tur swe-vie swe-zho_Hans tam-eng tat-eng tel-eng tgl_Latn-eng tha-ara tha-bul tha-ces tha-dan tha-deu tha-ell tha-eng tha-eng_ze tha-fas tha-fin tha-fra tha-heb tha-hrv tha-hun tha-ind tha-ita tha-kor tha-nld tha-nor tha-pol tha-por tha-por_BR tha-por_MZ tha-ron tha-rus tha-spa tha-spa_419 tha-spa_ES tha-srp tha-swe tha-tur tha-vie tur-ara tur-bos tur-bul tur-ces tur-dan tur-deu tur-ell tur-eng tur-eng_ze tur-est tur-fas tur-fin tur-fra tur-hbs_Latn tur-heb tur-hrv tur-hun tur-ind tur-ita tur-jpn tur-kor tur-lit tur-msa tur-nld tur-nor tur-pol tur-por tur-por_BR tur-por_MZ tur-ron tur-rus tur-slk tur-slv tur-spa tur-spa_419 tur-spa_ES tur-srp tur-srp_Latn tur-swe tur-tha tur-ukr tur-vie tur-zho_Hans ukr-bul ukr-ces ukr-deu ukr-eng ukr-eng_ze ukr-fra ukr-heb ukr-hrv ukr-hun ukr-ita ukr-nld ukr-nor ukr-pol ukr-por ukr-rus ukr-slv ukr-spa ukr-tur urd-eng uzb_Latn-eng vie-ara vie-bul vie-ces vie-dan vie-deu vie-ell vie-eng vie-eng_ze vie-est vie-fas vie-fin vie-fra vie-heb vie-hrv vie-hun vie-ind vie-ita vie-kor vie-msa vie-nld vie-nor vie-pol vie-por vie-por_BR vie-por_MZ vie-ron vie-rus vie-spa vie-spa_419 vie-spa_ES vie-srp vie-swe vie-tha vie-tur zho_Hans-bul zho_Hans-deu zho_Hans-eng zho_Hans-fin zho_Hans-fra zho_Hans-hbs_Latn zho_Hans-heb zho_Hans-hun zho_Hans-ita zho_Hans-jpn zho_Hans-msa_Latn zho_Hans-nld zho_Hans-pol zho_Hans-por zho_Hans-rus zho_Hans-spa zho_Hans-swe zho_Hans-tur zho_Hant-eng zho_Hant-por



ifndef SENTMT_LANGPAIRS

  LUMI_DATAHOME := /scratch/project_462000964/MARMoT/data
  SENTMT_LANGPAIRS_FWD := $(sort $(basename $(strip $(notdir $(shell grep -E '^[0-9]{8}' ${LUMI_DATAHOME}/sentmt/*.stats | cut -f1 -d:)))))
  SENTMT_LANGPAIRS_REV := $(foreach l,${SENTMT_LANGPAIRS_FWD},$(call reverse,$l))
  SENTMT_LANGPAIRS     := $(sort ${SENTMT_LANGPAIRS_FWD} ${SENTMT_LANGPAIRS_REV})

endif


SENTMT_TASK_LANGPAIRS := $(shell echo '${SENTMT_LANGPAIRS}' | tr ' ' "\n" | sed 's/^\(...\)_[^-]*\-/\1-/' | tr "\n" ' ')


SENTMT_TASK_IDS    := $(patsubst %,sentmt_%,${SENTMT_LANGPAIRS})
SENTMT_TRAINDATA   := $(foreach l,${SENTMT_TASK_IDS},${TRANSLATE_TRAIN_SENT})



## weights and weight factors for data sampling

USE_DATASIZE_AS_TASK_WEIGHT := 1
SAMPLING_TEMP               := 2
DOCMT_WEIGHT_FACTORS        := $(foreach l,${DOCMT_TASK_IDS},1)
SENTMT_WEIGHT_FACTORS       := $(foreach l,${SENTMT_TASK_IDS},2)




## task definitions put together

TASK_IDS            := ${SENTMT_TASK_IDS}  ${DOCMT_TASK_IDS}
TASK_LANGPAIRS      := ${SENTMT_TASK_LANGPAIRS}
TASK_TRAINDATA      := ${SENTMT_TRAINDATA} ${DOCMT_TRAINDATA}
TASK_WEIGHT_FACTORS := ${SENTMT_WEIGHT_FACTORSS} ${DOCMT_WEIGHT_FACTORS}


# TEST_TASK_IDS       := ${SENTMT_TASK_IDS}
VALID_TASK_IDS      := ${DOCMT_TASK_IDS}



# vocabularies / tokenizers
VOCAB          := sent_doc
VOCAB_SRC_SIZE := 32704
VOCAB_TRG_SIZE := 16320


NR_OF_NODES      := 24
BATCH_SIZE       := 32768
GRADIENT_ACCUM   := 10
LOOK_AHEAD       := 10

VALID_FREQ       := 2500
SAVE_FREQ        := 2500
REPORT_FREQ      := 250





include ../../../make/marmot.mk


info:
	@echo "number of tasks: $(words ${TASK_IDS})"
	@echo "${VALID_TASK_NRS}"
	@echo "${MISSING_LANGPAIRS}"
	@echo "$(words ${TASKS}) $(words ${TASK_LANGPAIRS})"
	@echo "$(sort $(subst -, ,${MISSING_LANGPAIRS}))"
