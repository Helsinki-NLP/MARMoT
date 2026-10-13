# RFC-EVAL-ARTIFACTS — Shared Evaluation Artifact Naming and Publication

**Status:** Revised draft for eval3\
**Scope:** Evaluation artifact identities, naming, validation, publication, compression, and migration

## 1. Purpose and design principles

The eval3 pipeline should use consistent and unambiguous filenames for hypotheses, evaluation scores, inference statistics, and related artifacts.

The main design principles are:

1. Preserve the identity of the training task as defined in the MAMMOTH configuration.
2. Identify evaluation datasets explicitly, including their versions where necessary.
3. Use language identifiers from the evaluation dataset, independently of the training task's language identifiers.
4. Avoid inferring task semantics from task-name prefixes.
5. Separate artifact identity from artifact type and serialization format.
6. Support reuse of inference results when the effective inference computation is identical.
7. Publish only complete, validated outputs.
8. Support optional lossless compression of large artifacts.
9. Maintain sufficient provenance for reproducibility and performance analysis.

## 2. Canonical artifact basename

Every evaluation case has the following basename:

```
<taskname>.<testsetname>.<testset-sourcelanguage>.<testset-targetlanguage>
```

For example:

```
mt_swe-fra.wmt24pp.swe.fra_FR
mt_fra-srp.flores200.fra.srp_Cyrl
mt_fra-srp_Cyrl.flores200.fra.srp_Cyrl
docmt_por-eng.bouquet.por_BR.eng
docmt_swe-eng.flores200.swe.eng
```

The basename identifies an evaluation case. A file extension identifies the artifact produced for that case.

### 2.1. Training task name

`<taskname>` is the exact task key from the MAMMOTH training configuration, conventionally `train.yaml`.

Examples include:

```
mt_swe-fra
docmt_por-eng
denoise_fin-fin
zero_cat-glg
def_eng-eng
```

These prefixes are examples, not reserved keywords.

The evaluation pipeline MUST NOT derive the task type, source language, target language, or training weight by parsing conventions such as `mt_`, `zero_`, or `denoise_`.

Such information should be obtained from the structured training configuration or from explicit evaluation configuration.

The task's `src_tgt` metadata identifies its training language pair. The task's `weight` is preserved as metadata and may provide useful information about training exposure.

The original task name remains an opaque identifier.

### 2.2. Test-set name

`<testsetname>` identifies the evaluation dataset, including sufficient release, version, split, or variant information to distinguish different test collections.

Prefer informative names rather than ambiguous abbreviations.

Examples:

```
flores200
wmt24pp
bouquet
```

Names such as `wmt` should not be used when multiple WMT datasets or editions could be confused.

If two different test collections would otherwise have the same identifier, their names MUST be made distinct, for example by including their split or release.

The exact spelling and meaning of each identifier MUST be registered in the dataset configuration. A registered identifier must not subsequently be reused for a different collection of examples.

Names such as `flores200` are sufficient only when the registry fixes which split and version they refer to.

### 2.3. Test-set language identifiers

`<testset-sourcelanguage>` and `<testset-targetlanguage>` are language identifiers from the evaluation dataset, normalized to the project's canonical language-code convention.

The base language code should be the project's three-letter language identifier.

Additional script or regional distinctions use underscores:

```
eng
swe
fra
srp
srp_Cyrl
por_BR
fra_FR
```

When both script and region are needed, use a consistent registered ordering, preferably:

```
<language>_<Script>_<REGION>
```

For example:

```
srp_Cyrl_RS
```

Script identifiers use the standard four-letter script notation, and region identifiers use standard two-letter country codes where applicable.

Dataset-specific identifiers such as `pt-BR` should be mapped through an explicit language-code registry rather than transformed by ad hoc filename parsing.

The earlier notation `BR.por` is replaced by `por_BR`, and `FR.fra` by `fra_FR`.

Placeholder components such as `XX.` are no longer needed.

**The evaluation language identifiers must reflect the actual evaluation dataset, even when its distinctions are identical to those already present in the training task name.**

For example:

```
mt_fra-srp.flores200.fra.srp_Cyrl
mt_fra-srp_Cyrl.flores200.fra.srp_Cyrl
```

These are different training tasks evaluated on the same dataset language pair.

Conversely:

```
mt_swe-fra.flores200.swe.fra
mt_swe-fra.wmt24pp.swe.fra_FR
```

identifies the same training task evaluated on datasets with different target-language specifications.

No special `__` refinement syntax is needed.

### 2.4. Filename restrictions

Test-set identifiers and language identifiers must not contain dots, directory separators, or characters with special filesystem meanings.

Task names should be preserved literally when they are safe as filename components. Any exceptional task names requiring escaping must use a documented, reversible encoding that preserves their original identity.

When parsing basenames, implementations must respect the registered suffix formats and parse the three evaluation components from the right. They must not rely on arbitrary assumptions about the internal spelling of task names.

## 3. Task selection is separate from artifact naming

The existence of a task in `train.yaml` does not imply that it should be evaluated.

The eval3 configuration should support explicit task lists, inclusion patterns, and exclusion patterns.

Task selection is conceptually independent of artifact naming.

In particular, the evaluator must not assume that every task is machine translation merely because it contains a source and target language.

Supported models may include:

- Machine translation and document translation
- Denoising and autoencoding
- Summarization and paraphrasing
- Definition generation
- Question answering
- Other sequence-to-sequence tasks

The selection policy, precedence rules, and default behavior are delegated to **RFC-EVAL-SELECTION**.

The selected task must be associated with a compatible evaluation dataset and evaluation procedure.

Denoising is not necessarily equivalent to copying: evaluation with corrupted input and a clean reference measures something different from clean-input reconstruction. Such tasks must not enter ordinary machine-translation evaluation accidentally.

## 4. Output directories and extensions

An evaluation artifact has a common basename and a type-specific extension.

### 4.1. Hypotheses

```
evaluation/hypotheses/<basename>.hyp
evaluation/hypotheses/<basename>.hyp.gz
```

Examples:

```
evaluation/hypotheses/mt_swe-fra.flores200.swe.fra.hyp

evaluation/hypotheses/mt_swe-fra.wmt24pp.swe.fra_FR.hyp.gz

evaluation/hypotheses/docmt_por-eng.bouquet.por_BR.eng.hyp.gz
```

`.hyp` contains one generated hypothesis per input sentence or registered evaluation unit.

`.hyp.gz` contains the same logical content compressed using gzip.

Compression must not alter the text, order, or number of hypotheses.

### 4.2. Corpus-level evaluation scores

Score outputs use:

```
evaluation/scores/<basename>.<score-extension>
```

For example:

```
evaluation/scores/mt_swe-fra.flores200.swe.fra.sacre

evaluation/scores/mt_swe-fra.flores200.swe.fra.bleu

evaluation/scores/mt_swe-fra.flores200.swe.fra.chrf
```

The exact set of supported score extensions is not fixed by this RFC.

However, **once an extension is used, its meaning must be defined and stable.**

For example, `.sacre` should refer to a registered SacreBLEU-based output convention, rather than arbitrarily changing between incompatible formats.

### 4.3. SacreBLEU output with metadata

The existing practice of prepending human-readable metadata to the machine-readable SacreBLEU JSON is permitted.

For example, a `.sacre` file may contain information about the dataset, task, inference configuration, and scoring command before the JSON payload.

Readers MUST NOT assume that JSON begins at byte zero.

A new writer SHOULD provide a recognizable boundary between the metadata preamble and the JSON payload. Readers may also support existing legacy preambles.

The machine-readable score payload must remain recoverable without depending on the exact wording of the human-readable preamble.

The `.sacre` extension need not be changed merely because this metadata is included.

## 5. Versioned COMET scoring

The extension `.comet` alone is potentially ambiguous because different COMET checkpoints, model versions, and scoring procedures can produce different scores.

This RFC does not prescribe a particular COMET model or require one universal filename suffix.

It does require that distinct scoring profiles are distinguishable and that every suffix used has a fixed meaning.

A possible convention is:

```
<basename>.comet.<scorer-id>.json
```

For example:

```
mt_swe-fra.flores200.swe.fra.comet.wmt22-comet-da.json

mt_swe-fra.flores200.swe.fra.comet.wmt20-comet-da.json
```

Here, `wmt22-comet-da` and `wmt20-comet-da` identify registered scoring profiles, not just informal model families.

Each scoring profile should resolve to an immutable specification including, as applicable:

- Model name and exact checkpoint or revision
- Scorer implementation and relevant version
- Reference-based or reference-free scoring procedure
- Relevant preprocessing and aggregation settings

A short scorer identifier can be used in the filename while the complete specification is maintained in the scoring configuration or provenance metadata.

Changing the checkpoint or scoring semantics requires a new profile identity.

An existing `.comet` file may be accepted during migration if its exact scoring configuration can be determined. New ambiguous `.comet` outputs should be avoided.

Other metrics can use analogous conventions when model or version distinctions affect their meaning.

## 6. Sentence-level scores

Sentence-level scores may be useful for error analysis, filtering, comparison of checkpoints, and subsequent research.

A possible naming convention is:

```
evaluation/scores/<basename>.sacre.tsv
evaluation/scores/<basename>.comet.<scorer-id>.tsv
```

Compressed variants may use `.tsv.gz`.

For example:

```
evaluation/scores/mt_swe-fra.flores200.swe.fra.comet.wmt22-comet-da.tsv.gz
```

The content, column names, sentence identifiers, treatment of multiple references, missing scores, and relationship between sentence-level and corpus-level scores will be specified separately in **RFC-EVAL-SCORES**.

This RFC only reserves a coherent naming pattern. It does not require the production of sentence-level scores.

## 7. Inference logs and performance statistics

Inference logs contain useful information about inference performance, including elapsed times and input/output token counts.

These measurements may support later analysis of MAMMOTH inference performance with respect to:

- Model architecture and parameter count
- Task and language pair
- Input and generated output lengths
- Tokenization
- Decoding configuration, including beam search
- Batch size and inference scheduling
- GPU hardware and execution environment

The raw logs may be substantially larger than the translation hypotheses or aggregate scores.

A tool already exists for extracting sentence-level performance statistics from these logs.

### 7.1. Structured run statistics

Proposed filename:

```
runs/<basename>.tsv
runs/<basename>.tsv.gz
```

For example:

```
runs/mt_swe-fra.flores200.swe.fra.tsv.gz
```

Such a file may describe individual sentences, inference batches, or the complete evaluation case.

The precise columns and measurement definitions will be specified in a separate **RFC-EVAL-RUNS**.

Potential measurements include input tokens, output tokens, elapsed inference time, batch information, and aggregated throughput.

Care is needed when attributing batched inference time to individual sentences. A batch duration is not automatically an independently measured duration for every sentence in that batch.

Similarly, token counts must identify the tokenizer or counting convention used.

No particular TSV schema is mandated here.

### 7.2. Raw logs

Raw inference logs should remain available independently of extracted statistics, at least for runs retained for reproducibility or performance research.

Logs may cover multiple evaluation cases within one Slurm job. They should therefore retain their execution or job identity rather than necessarily use a single evaluation-case basename.

A possible location is:

```
runs/logs/<run-id>.log.gz
```

Run identifiers should be associated with relevant evaluation cases through provenance records.

Once the raw logs have been retained, additional statistics can be extracted later without rerunning inference.

### 7.3. Reused inference and performance accounting

If one inference result is reused for multiple evaluation cases, the associated computation must not be counted as a new independent inference run.

Performance records should identify the original execution.

This prevents duplicated throughput or computation-time measurements when analyzing reused results.

## 8. Compression policy

Large completed artifacts may be stored in gzip-compressed form.

Compression is particularly useful for:

- Raw inference and Slurm logs
- Hypothesis files
- Sentence-level evaluation scores
- Inference monitoring and performance TSV files

For text-based artifacts, `.gz` is an optional compression suffix placed after the complete ordinary extension.

Examples:

```
.hyp.gz
.log.gz
.tsv.gz
.comet.<scorer-id>.tsv.gz
```

Compression must be lossless and transparent to consumers.

Readers should recognize both compressed and uncompressed variants.

For a given logical artifact, the pipeline should identify one authoritative completed output. If both variants exist, it must not silently choose between conflicting contents.

Compression policy may differ between artifact types. Small corpus-level score summaries do not necessarily benefit from compression.

New pipeline components SHOULD support direct production or reading of gzip files where practical.

Existing uncompressed artifacts need not be converted immediately.

## 9. Validation and atomic publication

A completed artifact must never become visible at its final path before it has passed the required validation.

The pipeline should distinguish:

1. Preflight checks, performed before generating output
2. Validation of the generated temporary artifact
3. Atomic publication of the validated artifact

### 9.1. Preflight validation

Before starting inference, check:

- The training task exists and its configuration can be resolved.
- The test-set identifier and language pair are registered.
- The required source and reference files exist.
- Their formats and cardinalities agree with the dataset specification.
- The source/reference language mapping is compatible with the selected task and evaluation procedure.
- The model checkpoint and decoding configuration are available.
- An equivalent validated artifact does not already exist and qualify for reuse.
- The target directory and temporary publication path are usable.

Where input checksums or version identifiers are available, retain them for provenance and reuse decisions.

A reference file is required for reference-based scoring, but not necessarily for every inference-only application.

Preflight checks should prevent predictable inference failures before expensive computation begins.

### 9.2. Temporary filenames

Inference must write to a temporary file rather than directly to the final `.hyp` path.

Suggested naming convention:

```
<basename>.hyp.tmp.<run-id>
```

For compressed output:

```
<basename>.hyp.gz.tmp.<run-id>
```

For example:

```
evaluation/hypotheses/
  mt_swe-fra.flores200.swe.fra.hyp.gz.tmp.22494799
```

`<run-id>` should be unique among concurrent writers, for example by combining the Slurm job ID with a process ID or another unique token.

Temporary files SHOULD reside in the destination directory or elsewhere on the same filesystem, so that the final rename can be atomic.

The `.tmp` marker makes unfinished outputs distinguishable from completed outputs.

The same convention applies to score files and structured run-statistics files.

### 9.3. Validation before publication

After inference finishes, but before the temporary file is renamed:

- Confirm that the inference process completed successfully.
- Confirm that the expected number of hypotheses was generated.
- Confirm that every output record is present and correctly formatted.
- Confirm that source, reference, and hypothesis cardinalities agree when reference-based evaluation is intended.
- Verify that any compressed output can be decoded and validated.
- Verify that the artifact corresponds to the intended dataset and task.
- Record or verify the relevant provenance and input identity.

For newline-delimited hypothesis files, the registered cardinality must match the number of logical hypothesis records.

These checks may be integrated into a streaming writer, avoiding a separate complete read after inference.

If output is compressed, validation must apply to its decompressed logical contents. The gzip stream must also be complete and valid.

**Output validation cannot generally be completed before output generation. It can, however, be completed before final publication.**

Once the validated file has been published, ordinary downstream consumers should not need to repeat the complete line-count validation each time it is read.

### 9.4. Atomic publication

A successful output follows this lifecycle:

```
preflight
   |
   v
write temporary output
   |
   v
finish and validate output
   |
   v
optionally compress and validate
   |
   v
atomically rename to final filename
   |
   v
completed artifact available
```

Examples of final publication:

```
file.hyp.tmp.<run-id>     -> file.hyp

file.hyp.gz.tmp.<run-id>  -> file.hyp.gz

file.sacre.tmp.<run-id>   -> file.sacre
```

The rename must occur on the same filesystem.

Concurrent writers must be coordinated so that publication cannot silently overwrite a different completed artifact. Existing valid outputs should normally be reused rather than overwritten.

An invalid or interrupted temporary output must never be renamed to its final filename.

Failed temporary outputs may be removed or retained for debugging according to the pipeline's cleanup policy.

The same publication principle applies to scores and run-statistics files, with artifact-specific validation.

For strict crash durability, implementations may additionally flush and synchronize output data and relevant directory metadata before and after publication.

### 9.5. Existing completed files

A completed file is not automatically reusable merely because its filename exists.

Reuse requires that it matches the expected identity and provenance, including the relevant model, inputs, decoding configuration, and artifact type.

Completed artifacts should normally be treated as immutable.

Regeneration with changed inputs or settings must not silently replace an existing artifact whose basename does not distinguish the change.

Where filenames are insufficient to capture all dependencies, the pipeline must use the configured provenance and cache-validation rules.

## 10. Dataset cardinalities and provenance

The dataset registry is authoritative for expected cardinalities.

Previously used evaluation datasets have included the following counts:

| Legacy dataset identifier | Recorded line count |
| ------------------------- | ------------------- |
| `bqt`                     | 854                 |
| `bqtpar`                  | 436                 |
| `flo`                     | 1012                |
| `wmt`                     | 960                 |

These counts describe the dataset versions currently used by eval2. They must not automatically be assumed to apply to every release or split associated with a new, more descriptive test-set name.

Migration to names such as `flores200`, `wmt24pp`, or `bouquet` requires explicit verification of the corresponding dataset version and data files.

The dataset registry SHOULD record:

- Canonical test-set identifier
- Original dataset and release/version
- Split, subset, or filtering variant
- Source and target language identifiers
- Source and reference locations
- Expected number of evaluation units
- Input checksums where practical

The expected cardinality should be available before inference begins.

The hypothesis writer should verify that the actual output cardinality matches the expectation before publication.

This avoids depending on retrospective validation of already-published files.

## 11. Reusing inference results

The filename identifies the evaluation case, but this need not uniquely identify the underlying computation.

Two evaluation cases may share an inference result if their **effective inference inputs and computation are identical**.

Relevant conditions include:

- The same model checkpoint
- Identical prepared source inputs, in the same order
- Identical effective task routing and control tokens
- Identical preprocessing and tokenizer behavior
- Identical decoding configuration
- Identical generation settings, including random-seed requirements where relevant

The dataset name alone does not determine whether the inputs are identical.

For example, two test sets may use identical source sentences but different references or evaluation annotations.

Such cases can share inference while retaining separate evaluation identities and scoring outputs.

The pipeline should detect safe reuse through provenance and input identity, not through superficial similarities between filenames.

Likewise, different target-language refinements do not necessarily require another inference run when the effective inference computation is unchanged.

Reuse may be implemented with a shared inference cache, references to an existing artifact, or another mechanism that preserves the evaluation-case interface.

The details belong in the inference planning and cache specification.

## 12. Migration from eval2

The new naming convention replaces the eval2 representation of language metadata.

For illustration, assuming the corresponding test-set identities have been verified:

| Training task     | Legacy eval2 task       | New basename                             |
| ----------------- | ----------------------- | ---------------------------------------- |
| `mt_swe-fra`      | `mt_XX.swe-FR.fra`      | `mt_swe-fra.wmt24pp.swe.fra_FR`          |
| `mt_fra-srp`      | `mt_XX.fra-XX.srp_Cyrl` | `mt_fra-srp.flores200.fra.srp_Cyrl`      |
| `mt_fra-srp_Cyrl` | `mt_XX.fra-XX.srp_Cyrl` | `mt_fra-srp_Cyrl.flores200.fra.srp_Cyrl` |
| `docmt_por-eng`   | `docmt_BR.por-XX.eng`   | `docmt_por-eng.bouquet.por_BR.eng`       |
| `docmt_swe-eng`   | `docmt_XX.swe-XX.eng`   | `docmt_swe-eng.flores200.swe.eng`        |

The dataset assignments in this table are illustrative. Actual migrations must use the dataset registry, not infer the new dataset identifier from the old evaluation-task name.

Legacy artifact extensions, including `.0shyp` and `.0ssacre`, may be recognized by migration tools.

Training weights should be obtained from the training metadata rather than inferred from these extensions.

Migration should:

1. Resolve the original training task and dataset.
2. Resolve the dataset's source and target language identifiers.
3. Verify the artifact's relationship to the intended model and inference configuration.
4. Validate the legacy output and its dataset cardinality.
5. Produce or register the corresponding new artifact path.
6. Preserve the score format and scorer identity where known.
7. Avoid unnecessary retranslations.

Some eval2 filenames may not uniquely identify their training task, dataset, or scoring configuration. These cases require additional metadata or inspection.

Migration must report unresolved ambiguities rather than guessing.

Existing valid inference results should be reused wherever possible.

If multiple legacy files map to the same new artifact path, the migration must check whether their contents and provenance agree. Conflicting files must not silently overwrite one another.

## 13. Relationship to evaluation configuration

The canonical filename encodes:

```
training task
evaluation dataset
evaluation source language
evaluation target language
artifact type
```

It does not attempt to encode every aspect of reproducibility.

Additional metadata may include:

```
model checkpoint
training configuration
task weight
dataset version and checksums
tokenizer and preprocessing
decoding settings
scorer checkpoint and configuration
software environment
run identifier
hardware
execution times
```

The pipeline should maintain a reliable mapping between published artifacts, their generating configurations, and their provenance.

Filenames should remain reasonably short and readable. They are identifiers, not substitutes for complete run metadata.

## 14. Related specifications

The following companion RFCs are proposed:

- **RFC-EVAL-YAML** — Training configuration and generated inference YAML interface
- **RFC-EVAL-SELECTION** — Task lists, patterns, precedence, exclusions, and defaults
- **RFC-EVAL-DATASETS** — Dataset registry, versioning, language codes, reference files, and cardinalities
- **RFC-EVAL-SCORES** — Scoring profiles, machine-readable score payloads, metadata preambles, and sentence-level score formats
- **RFC-EVAL-RUNS** — Inference performance statistics, token counts, timing definitions, raw-log retention, and provenance
- **RFC-EVAL-CACHE** — Inference identity, reusable outputs, cache validity, and duplicate-work elimination

## 15. Summary of the proposed convention

The central convention is:

```
<taskname>.<testsetname>.<testset-src>.<testset-tgt>
```

With extensions identifying the resulting artifacts:

```
evaluation/hypotheses/<basename>.hyp[.gz]

evaluation/scores/<basename>.sacre

evaluation/scores/<basename>.comet.<scorer-id>.json

evaluation/scores/<basename>.comet.<scorer-id>.tsv[.gz]

runs/<basename>.tsv[.gz]
```

The essential invariants are:

1. Training task names are preserved.
2. Evaluation languages describe the actual dataset.
3. Test-set identifiers have fixed, registered meanings.
4. Extensions and scoring profiles have fixed meanings.
5. Published artifacts are complete and validated.
6. Compression does not change artifact identity or content.
7. Equivalent inference computations may share results.
8. Provenance is maintained separately from readable filenames.

The resulting convention removes the need for `XX.` placeholders, special `__` refinements, and task-prefix heuristics while providing a stable interface for inference, scoring, monitoring, and later analysis.

## Three design decisions worth retaining

1\. The basename is an evaluation identity, not a computation identity. This is the most important distinction for avoiding duplicate inference. Two basenames may refer to different scoring cases but share the same inference computation. Conversely, two runs with the same basename but different checkpoints cannot safely be treated as interchangeable.

2\. The atomic-output protocol belongs in the shared RFC. Otherwise each script in eval3 may invent its own treatment of incomplete files. Temporary-file creation, validation, compression, and final publication should be implemented in a small shared utility rather than repeated in inference and scoring scripts.

3\. The largest remaining architectural question is checkpoint identity. Your proposed basename deliberately omits model identity, which is appropriate when each model has its own evaluation directory. If eval3 ever stores outputs for multiple checkpoints in the same directory, it will need an additional namespace or directory level. I would preserve the four-component basename and resolve that issue through directory structure rather than lengthening every filename.

The revised RFC leaves sentence-level TSV schemas open while making their filenames predictable. It also accommodates extracting performance measurements from existing inference logs, without committing the pipeline to collecting measurements that are not actually observable.
