
# MAMMOTH models - architecture search

Experiments with several architecture variants. All models are trained on MultiSynt data produced by OPUS-MT, document/paragraph-level with context window of max 1024 tokens. Tasks are translation tasks with English and Spanish as the central pivot language (both directions). We use the same batch size for gradient updates (roughly 320k tokens, some differences in actual batch size and batch accumulation) and the same learning parameters. The vocabularies are based on language-specific tokenizers of size 32k unless specified with other values.


## Naming conventions:

* general model name pattern: `ENC-DEC-PARAM`
* `ENC` refers to the encoder structure
* `DEC` refers to the decoder structure
* `PARAM` refers to other architectural choices

The encoder and decoder specifications follow the following naming template: `VX[SY]*`.
* `V` is the vocabulary sharing strategy and `X` is the size of that vocabulary (roughly in thousands or K)
* `S` is the sharing strategy of a component in the encoder/decoder and `Y` is the size of that component (in layers)

Sharing strategies are:
* `l` for language-specific components
* `g` for language-group-specific components
* `a` for completely shared components ("all")

Other parameters:
* `hX`: number of attention heads = `X`
* `dX`: dimensionality = `X`

