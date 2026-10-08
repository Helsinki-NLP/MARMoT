# dashboard: MAMMOTH training dashboard

A small PHP web application that plots the validation and evaluation scores of
the models in [`models/`](../models/README.md). It lets you pick an experiment
group, filter the models and tasks, and compare their scores over training.

## Running it

The dashboard is plain PHP with no build step. Serve the directory with any PHP
web server, for example:

```bash
cd dashboard
php -S localhost:8000
```

then open <http://localhost:8000/>.

The page does not read the model files from the local checkout. It fetches them
from GitHub using the raw URL defined at the top of [`index.php`](index.php):

```php
define('MARMOT_GIT_RAW', 'https://raw.githubusercontent.com/Helsinki-NLP/MARMoT/refs/heads/main');
```

This means the scores shown are always those committed to `main` on GitHub, and
the server needs outbound network access to GitHub and to the Plotly CDN. To
develop against local (uncommitted) score files, point `MARMOT_GIT_RAW` at a
local directory or another branch.

## What it reads

From `models/<experiment>/<model>/stats/`:

| File | Use |
| --- | --- |
| `valid-scores-bleu.txt` | BLEU validation scores |
| `valid-scores-chrf.txt` | chrF validation scores |
| `valid-scores-ppl.txt` | perplexity (drawn on a log axis, sorted the other way) |
| `train-progress.txt` | training progress, used to plot scores per consumed tokens or training time |

The list of experiment directories comes from
[`models/experiments.txt`](../models/experiments.txt); the default is `hpo`.
These files are maintained by the makefiles in [`models/`](../models/README.md).

## Features

* Choose the experiment directory and filter models by their name components
  (size, tasks, sharing, ...), task type, and language/language pair.
* Select which models and tasks to plot.
* Switch the metric (BLEU / chrF / perplexity) and the x axis (training steps,
  training time, or consumed tokens).
* A comparison bar chart for one model (or all selected models) at a chosen
  checkpoint, optionally showing the difference between checkpoints.

## Files

| File | Purpose |
| --- | --- |
| [`index.php`](index.php) | Entry point. Reads the request parameters, loads the score files, and assembles the HTML. It also answers the small JSON requests used to refresh the model/task lists (`updatelists`) and to fetch one model's bar-chart data (`barchartdata`) before any page output is written. |
| [`functions.php`](functions.php) | All functions: reading score files, computing budget-normalised scores, building the selection forms, and rendering the Plotly charts. |
| [`script.js`](script.js) | Behaviour in the browser: model/task selection, and trimming the bar-chart payload to the tasks the filters leave. |
| [`style.css`](style.css) | Styles, including the collapsible filter and selection blocks. |

The implementation is split by concern: `index.php` drives the flow,
`functions.php` holds the logic and rendering, `script.js` is the client-side
behaviour, and only the per-request data (scores and bar-chart task list) is
emitted inline in the HTML.