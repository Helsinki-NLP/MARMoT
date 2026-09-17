
# MAMMOTH models


## Naming conventions:

* all model names follow this name structure: <model>-<tasks>-<enc>-<dec>-<batch>
* `model`: small, base, big, xl
* `task`: 1p = English-centric, 2p = English/French-centric, 3p = English/French/Spanish-centric, 4p = English/French/Spanish/German-centric, d = denoising
* `enc`: encoder components, L = language-specific, G = shared across language groups, A = shared across all
* `dec`: decoder components, L = language-specific, G = shared across language groups, A = shared across all
* `batch`: approximate size of batches for graident updates (multiplying batch size and batch accumulation)




## English-centric models


Transformer-small:

* small-1p+d-LAenc-Ldec-320k
* small-1p+d-Lenc-Ldec-320k


Transformer-base models with language-specific encoders and decoders:

* base-1p+d-Lenc-Ldec-320k
* base-1p+d-Lenc-Ldec-640k


Transformer-base models with different types of parameter sharing:

* base-1p+d-Aenc-Ldec-320k
* base-1p+d-Aenc-Ldec-640k
* base-1p+d-GAenc-Ldec-320k
* base-1p+d-Genc-Ldec-320k
* base-1p+d-LAenc-Ldec-320k
* base-1p+d-LGAenc-Ldec-320k


Bigger transformer models with language-specific encoders and decoders:


* big-1p+d-Lenc-Ldec-100k
* big-1p+d-Lenc-Ldec-320k
* xl-1p+d-Aenc-Ldec-100k
* xl-1p+d-Aenc-Ldec-320k


## English/French-centric models


* base-2p+d-Aenc-Ldec-640k
* base-2p+d-Lenc-Ldec-320k
* base-2p+d-Lenc-Ldec-640k



## English/French-centric models

Note that here we replace French with Spanish as the second pivot language!

* big-2p+d-GAenc-Ldec-320k
* big-2p-GAenc-Ldec-320k (continuation of big-2p+d-GAenc-Ldec-320k but no denoising tasks!)




## English/French/Spanish/German-centric models

Different model sizes with language-specific encoders and decoders


* small-4p+d-Lenc-Ldec-960k
* base-4p+d-Lenc-Ldec-640k
* big-4p+d-Lenc-Ldec-160k
* xl-4p+d-Lenc-Ldec-20k


Different model sizes with fully-shared encoders and language-specific decoders:

* small-4p+d-Aenc-Ldec-960k
* base-4p+d-Aenc-Ldec-640k
* big-4p+d-Aenc-Ldec-160k
* xl-4p+d-Aenc-Ldec-20k


Different model sizes with encoders shared across language-groups and language-specific decoders:


* small-4p+d-Genc-Ldec-960k
* base-4p+d-Genc-Ldec-640k
* big-4p+d-Genc-Ldec-160k
* xl-4p+d-Genc-Ldec-20k


Transformer-base models with other types of parameter sharing:

* base-4p+d-LAenc-Ldec-640k
* base-4p+d-GAenc-Ldec-640k


Failed runs:

* base-4p+d-Aenc-Adec-640k
* base-4p+d-LAenc-LAdec-640k
* base-4p+d-GAenc-GAdec-640k


