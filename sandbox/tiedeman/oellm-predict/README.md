
# Multilingual Models using OpenEuroLLM languages


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

