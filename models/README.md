

# Mammoth Models


Training with only monolingual pre-training tasks:

* predict-sharedenc:
  - transformer-base model with fully shared encoder (but language-specific vocabs) and language-specific decoders
  - trained on monolingual text prediction tasks using MultiSynt data
  - STATUS: queued
* denoise-predict-sharedenc:
  - transformer-base model with fully shared encoder (but language-specific vocabs) and language-specific decoders
  - trained on monolingual denoising and text prediction tasks using MultiSynt data
  - STATUS: running



Training on English-centric machine translatino tasks + monolingual denoising:

* docmt-denoise:
  - transfomer-base model with language-specific encoders and decoders
  - STATUS: running
* docmt-denoise-sharedenc:
  - transfomer-base model with fully-shared encoders and language-specific decoders
  - STATUS: running
* docmt-denoise-halfsharedenc:
  - transfomer-base model with partially shared encoders (3 language-specific layers + 3 fully-shared layers) and language-specific decoders
  - STATUS: running
* docmt-denoise-LGAenc:
  - transfomer-base model with partially shared encoders (2 language-specific layers + 2 language-group-specific layers + 2 fully-shared layers) and language-specific decoders
  - STATUS: running
* docmt-denoise-small:
  - transfomer-small model with language-specific encoders and decoders
  - STATUS: running
* docmt-denoise-tiny:
  - transfomer-tiny model with language-specific encoders and decoders
  - STATUS: queued



Training on English-centric MT tasks without additional denoising tasks:

* docmt-sharedenc:
  - transfomer-base model with fully shared encoder (but language-specific vocabs) and language-specific decoders
  - STATUS: 2-day training done?
  - NOTE: training logfile was over-written for some strange reason --> validation results are lost



Training on additional language pairs using more than just English-centric data (without denoising tasks):

* docmt-2pivots:
  - transfomer-base model with language-specific encoders and decoders
  - English/French-centric MultiSynt data (without denoising tasks) + 2 additional language pairs to fill compute nodes
  - STATUS: running
* docmt-4pivots:
  - transfomer-base model with language-specific encoders and decoders
  - German/English/French/Spanish-centric MultiSynt data (without denoising tasks) + 4 additional language pairs to fill compute nodes
  - STATUS: 2-day training done
  