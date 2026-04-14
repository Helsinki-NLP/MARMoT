

# Mammoth Models


* denoise-predict-sharedenc:
  - transformer-base model with fully shared encoder (but language-specific vocabs) and language-specific decoders
  - trained on monolingual denoising and text prediction tasks using MultiSynt data
  - STATUS: queued
* docmt-denoise:
  - transfomer-base model with language-specific encoders and decoders
  - trained on English-centric translation tasks and monolingual denoising tasks using MultiSynt data
  - STATUS: queued
* docmt-sharedenc:
  - transfomer-base model with fully shared encoder (but language-specific vocabs) and language-specific decoders
  - trained on English-centric translation tasks using MultiSynt data
  - STATUS: 2-day training done?
  - NOTE: training logfile was over-written for some strange reason --> validation results are lost
* docmt-4pivots-lang:
  - transfomer-base model with language-specific encoders and decoders
  - trained on German/English/French/Spanish-centric MultiSynt data
  - STATUS: 2-day training done
* mammoth-flan:
  - transfomer-large model (12x12) with encoders shared across language groups and language-specific decoders
  - curriculum-based training: (1) denoising, (2) text prediction, (3) MT, (4) FLAN
  - run on 4 nodes only (heavy GPU sharing in later training stages)
  - STATUS: quite slow and just first stage is done