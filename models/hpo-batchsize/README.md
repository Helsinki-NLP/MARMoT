
# MAMMOTH models


## English-centric models


Transformer-base models with language-specific encoders and decoders and different batch sizes:

* docmt-1pivot-denoise-base-nobatchaccum: no gradient accumulation
* docmt-1pivot-denoise-base-smallbatch: small batches but gradient accumulation = 20
* docmt-1pivot-denoise-base-mediumbatch: medium-sized batches but gradient accumulation = 20
* docmt-1pivot-denoise-base-accum10: full-sized batch but gradient accumulation = 10
* docmt-1pivot-denoise-base-320k-contd: continuation of accum10 training

