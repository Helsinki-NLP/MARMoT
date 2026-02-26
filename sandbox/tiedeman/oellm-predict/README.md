
# Multilingual Models using OpenEuroLLM languages


Models aree trained on synthetic training data (translations of Nemotron-CC-HQ from English into 36 other languages). The data prepared for mammoth training is in `/scratch/project_462000964/MARMoT/data/multisynt` on LUMI:

* `train/len1024`: parallel data for translation tasks with context size <= 1024 characters
* `textpredict/train/len1024`: text prediction data with a sliding window across documents of context size <= 1024 characters



## Successfully Trained Models

Model variants below use English-centric translation tasks (in both directions), monolingual text prediction tasks (denoted by `predict`), denoising autoencoder tasks, and/or cross-lingual text prediction tasks (marked as `crosspredict`).


Tranformer-based models (6x6 layers) with language-specific encoders and decoders that have successfully been trained for 48 hours (sub-directoy names):

* `oellm-predict`: monolingual text prediction
* `oellm-translate2-36`: English-centric translation tasks
* `oellm-predict-denoise-translate2`: monolingual text prediction, denoising, translation
* ` oellm-crosspredict-denoise-translate2`: monolingual and cross-lingual text prediction, denoising, translation

Note that some encoders are shared for languages that are considered variants of some metalanguage defined by by the ISO standard for language groups.



Tranformer-based models (6x6 layers) with **fully shared** encoders and decoders that have successfully been trained for (at least) 48 hours (sub-directoy names):

* `oellm_shared-translate2-36`: English-centric translation tasks
* `oellm_shared-crosspredict-denoise-translate2-36`: monolingual and cross-lingual text prediction, denoising, translation


Tranformer-based models (6x6 layers) with **fully shared** encoders and **language-specific** decoders that have successfully been trained for (at least) 48 hours (sub-directoy names):


* `oellm_sharedenc-translate2-36`: English-centric translation tasks
* `oellm_sharedenc-crosspredict-denoise-translate2-36`: monolingual and cross-lingual text prediction, denoising, translation



## Models that crashed

All other model variants crashed so far. Some interesting cases for debugging are:

* `oellm_12x12-translate2-36`: The same model as `oellm-translate2-36` but with a larger transformer model (12x12 layers)
* ` oellm_Genc6x6-translate2`: The same model as `oellm-translate2-36` but with a partially shared encoder across languages that come from the same language group (grand-parent of the language according to ISO standard, e.g. Germanic languages etc)







# UNFINISHED DOCUMENTATION



Model variants:

## oellm-predict (default without target suffix)

* 32 monolingual text prediction tasks
* 6x6 transformer-base model
* encoders: meta-language
* decoders: language-specific


## oellm-predict-partially-shared

* make target suffix: .partiall-shared
* 32 monolingual text prediction tasks
* 6x6 transformer-base model
* encoders: 3 layers meta-language, 3 layers shared for all
* decoders: 3 layers shared for all, 3 layers language-specific



## oellm-crosspredict

* make target suffix: .crosspredict
* 32 monolingual text prediction tasks
* 32 cross-lingual text prediction tasks (xxx to English)
* 6x6 transformer-base model
* encoders: meta-language
* decoders: language-specific


## oellm-predict-translate

* make target suffix: .partiall-shared
* 32 monolingual text prediction tasks
* 32 translation tasks from other languages to English
* 6x6 transformer-base model
* encoders: 3 layers meta-language, 3 layers shared for all
* decoders: 3 layers shared for all, 3 layers language-specific


## oellm-crosspredict-translate

* make target suffix: .partiall-shared
* 32 monolingual text prediction tasks
* 32 cross-lingual text prediction tasks (xxx to English)
* 32 translation tasks from other languages to English
* 6x6 transformer-base model
* encoders: 3 layers meta-language, 3 layers shared for all
* decoders: 3 layers shared for all, 3 layers language-specific

