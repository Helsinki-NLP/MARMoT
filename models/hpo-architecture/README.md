
# MAMMOTH models - architecture search

Experiments with several architecture variants. All models are trained on MultiSynt data produced by OPUS-MT, document/paragraph-level with context window of max 1024 tokens. Tasks are translation tasks with English and Spanish as the central pivot language (both directions). We use the same batch size for gradient updates (roughly 320k tokens, some differences in actual batch size and batch accumulation) and the same learning parameters. The vocabularies are based on language-specific tokenizers of size 32k unless specified with other values.


## Naming conventions:

* general model name pattern: `ENC-DEC-VOCAB-PARAM`
* `ENC` refers to the encoder structure
* `DEC` refers to the decoder structure
* `VOCAB` refers to vocabularies used on encoder and decoder side
* `PARAM` refers to other architectural choices

The encoder and decoder specifications follow the following naming template: `[sy]+`.
* `s` is the sharing strategy (see below) of a component in the encoder/decoder
* `y` is the size of that component (in layers)

Sharing strategies are:
* `L` for language-specific components
* `G` for language-group-specific components
* `A` for completely shared components ("all")

Vocabularies (`VOCAB`): `SxxTyy`
* `S` is the vocabulary sharing strategy for the encoder vocabulary
* `T` is the vocabulary sharing strategy for the decoder vocabulary
* `xx` and `yy` are the sizes of that vocabularies (roughly in thousands or K)

Other parameters (`PARAM`):
* `Hx`: number of attention heads = `x`
* `Dxxx`: dimensionality = `xxx`

