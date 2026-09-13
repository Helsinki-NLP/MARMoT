
# MAMMOTH models


## English-centric models


Transformer-small:

* docmt-1pivot-denoise-small-320k
* docmt-1pivot-denoise-halfsharedenc-small-320k


Transformer-base models with language-specific encoders and decoders:

* docmt-1pivot-denoise-base: gradient accumulation = 20
* docmt-1pivot-denoise-base-320k: gradient accumulation = 10
* docmt-1pivot-denoise-base-320k-contd: continuation of training
* docmt-1pivot-denoise-labels-base-320k: using language-tokens as labels (not very useful)


Transformer-base models with language-specific encoders and decoders and different batch sizes:

* docmt-1pivot-denoise-base-nobatchaccum: no gradient accumulation
* docmt-1pivot-denoise-base-smallbatch: small batches but gradient accumulation = 20
* docmt-1pivot-denoise-base-mediumbatch: medium-sized batches but gradient accumulation = 20
* docmt-1pivot-denoise-base-accum10: full-sized batch but gradient accumulation = 10


Transformer-base models with different types of parameter sharing:

* docmt-1pivot-denoise-sharedenc-base
* docmt-1pivot-denoise-sharedenc-base-320k
* docmt-1pivot-denoise-groupsharedenc-base-320k
* docmt-1pivot-denoise-groupsharedenc-labels-base-320k
* docmt-1pivot-denoise-halfsharedenc-base-320k
* docmt-1pivot-denoise-GAenc-base-320k
* docmt-1pivot-denoise-LGAenc-base-320k


Bigger transformer models with language-specific encoders and decoders:

* docmt-1pivot-denoise-big-100k
* docmt-1pivot-denoise-big-320k
* docmt-1pivot-denoise-xl-100k
* docmt-1pivot-denoise-xl-320k


## English/French-centric models

* docmt-2pivot-denoise-base
* docmt-2pivot-denoise-base-320k
* docmt-2pivot-denoise-sharedenc-base


## English/Spanish-centric models

* docmt-2pivot-denoise-GAenc-big


## English/French/Spanish-centric models

* docmt-3pivot-denoise-base
* docmt-3pivot-denoise-sharedenc-base


## English/French/Spanish/German-centric models

Different model sizes with language-specific encoders and decoders

* docmt-4pivot-denoise-small
* docmt-4pivot-denoise-base
* docmt-4pivot-denoise-big
* docmt-4pivot-denoise-xl


Different model sizes with fully-shared encoders and language-specific decoders:

* docmt-4pivot-denoise-sharedenc-small
* docmt-4pivot-denoise-sharedenc-base
* docmt-4pivot-denoise-sharedenc-big
* docmt-4pivot-denoise-sharedenc-xl


Different model sizes with encoders shared across language-groups and language-specific decoders:

* docmt-4pivot-denoise-groupsharedenc-small
* docmt-4pivot-denoise-groupsharedenc-base
* docmt-4pivot-denoise-groupsharedenc-big
* docmt-4pivot-denoise-groupsharedenc-xl


Transformer-base models with other types of parameter sharing:

* docmt-4pivot-denoise-halfsharedenc-base
* docmt-4pivot-denoise-halfgroupsharedenc-base


Failed runs:

* docmt-4pivot-denoise-halfgroupsharedenc-halfgroupshareddec-base
* docmt-4pivot-denoise-halfsharedenc-halfshareddec-base
* docmt-4pivot-denoise-sharedenc-shareddec-base


## other models

docmt-validzeroshot
