<?php

/*
    MAMMOTH training dashboard - entry point of the page.

    The implementation is split by language: this file holds the flow of the
    page (parameters, reading the data, html assembly), functions.php all the
    functions, style.css the styles and script.js the behaviour in the
    browser. What php has to hand to the browser for one request - the scores
    and the tasks of the bar chart - stays inline in the html, because it is
    data and differs with every request.

    Choosing another model in the bar chart drop-down asks this script for
    "barchartdata", and wants the scores of that one model as json and nothing
    else. The answer has to go out before a single byte of the page is written,
    otherwise the status line and content type arrive too late; that is why the
    request is dealt with here, above the html.
*/

require __DIR__.'/functions.php';

// where the scores live, and which score files may be read from it
define('MARMOT_GIT_RAW', 'https://raw.githubusercontent.com/Helsinki-NLP/MARMoT/refs/heads/main');
define('SCORE_FILES', array('valid-scores-bleu.txt', 'valid-scores-chrf.txt', 'valid-scores-ppl.txt'));
// drop-down value that charts every selected model of the page at once
define('BARCHART_ALL', '(all)');

if (isset($_REQUEST['barchartdata']) && $_REQUEST['barchartdata'] !== ''){
    barchart_json_response();
    exit;
}

?>
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">

<html>
<head>
  <title>MAMMOTH Training Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="style.css?v=<?php echo filemtime(__DIR__.'/style.css'); ?>"/>
  <script src="script.js?v=<?php echo filemtime(__DIR__.'/script.js'); ?>"></script>
</head>
<body>
<?php

/*
    MAMMOTH training dashboard
    -------------------------
    Reads validation scores and training statistics from the MARMoT repository
    on GitHub, lets you select models/tasks, and plots the scores with plotly.
*/

// number of "-"-separated components a model name may consist of
define('MODEL_COMPONENTS', 5);

if (isset($_POST['submit']) && $_POST['submit'] == 'reset'){
    $_POST = $_REQUEST = $_SESSION = array();
}

// which language filters to show
$SHOW_SOURCELANG_SELECTION = false;
$SHOW_TARGETLANG_SELECTION = false;
$SHOW_LANGPAIR_SELECTION   = true;

// ------------------------------------------------------------- parameters

$MarmotGitRaw      = 'https://raw.githubusercontent.com/Helsinki-NLP/MARMoT/refs/heads/main';
$expdir            = get_param('expdir', 'hpo');
$model_dir         = $MarmotGitRaw.'/models/'.$expdir;

// an unknown experiment directory is a user error, not a server error: the
// warning of the failing request is suppressed and reported in the page
$available_expdirs = @file($MarmotGitRaw.'/models/experiments.txt');
if ($available_expdirs === false) $available_expdirs = array();

$available_models = @file($model_dir.'/models.txt');
if ($available_models === false){
    $available_models = array();
    echo('<p><b>Error:</b> there is no experiment directory named <tt>'
        .htmlspecialchars($expdir).'</tt>. Known directories: <tt>'
        .htmlspecialchars(implode(', ', array_map('trim', $available_expdirs)))
        .'</tt>. Choose one of them in the form below.</p>');
}

$file  = get_param('file', 'valid-scores-bleu.txt');
$xaxis = get_param('xaxis', 'training-steps');
$barchart = get_param('barchart', ''); // model to show as bars, or BARCHART_ALL
$barchartidx = get_param('barchartidx', ''); // slider position, 0 = last
$barchartckpt = get_param('barchartckpt', 'last'); // or a checkpoint, for old links
$diff = get_param('diff', '') ? true : false; // bars as diff, not as score
$showmodels = get_param('showmodels', '1') ? '1' : '0'; // is the filter block expanded?
$showselmodels = get_param('showselmodels', '1') ? '1' : '0'; // is model selection expanded?
$showtasks = get_param('showtasks', '1') ? '1' : '0'; // is task selection expanded?

$models    = get_array_param('models');
$selmodels = get_array_param('selmodels'); // the checked models of the model selection

// the marker of the model selection block: it is on every page, so it is only
// missing when the block has never been submitted (or was reset away)
$selmodels_set = isset($_REQUEST['selmodels_set']);

$model_components = array();
for ($i = 0; $i < MODEL_COMPONENTS; $i++){
    $model_components[$i] = get_array_param('mcomp'.$i);
}

$tasks     = get_array_param('tasks');
$mtasks    = get_array_param('mtasks');
$types     = get_array_param('tasktypes');
$langs     = get_array_param('langs');
$srclangs  = get_array_param('srclangs');
$trglangs  = get_array_param('trglangs');
$langpairs = get_array_param('langpairs');

// $file ends up in the path of a file to read, so it is held to the three
// known score files rather than whatever the query string asks for
if (! in_array($file, SCORE_FILES)) $file = SCORE_FILES[0];
$metric = metric_label($file);

/*
    The bar chart of one model, as json on its own. This block is never reached
    for such a request: those are answered by barchart_json_response() at the
    top of the file, before any page output.
*/

// ---------------------------------------------- read scores for the models

$scores    = array();
$traintoks = array();
$traintime = array();

select_models($available_models, $models, $model_components);

/*
    The checkboxes of the model selection block narrow the filtered list down
    further. As long as that block has never been submitted, every filtered
    model counts as selected. A selection whose models are all gone from the
    filtered list was left behind by a changed filter, so it starts over with
    every model the filters let through.
*/

$filtered_models = $models;
if ($selmodels_set){
    if (count($selmodels) && ! array_intersect($selmodels, $filtered_models)){
        $selmodels = $filtered_models;
    }
    $models = array_values(array_intersect($filtered_models, $selmodels));
}

$nr_of_models        = count($models);
$available_tasks     = array('average-filtered' => $nr_of_models, 'average-selected' => $nr_of_models);
$available_tasktypes = array();
$available_srclangs  = array();
$available_trglangs  = array();

foreach ($models as $m){
    $model = rtrim($m);
    read_valid_scores($scores, $available_tasks, $available_srclangs, $available_trglangs,
                      $available_tasktypes, $model, $file, $model_dir);
}

// ------------------------------------------ filter, average and checkpoint

/*
    The tasks the filters leave, the model/task combinations that go into the
    plots and the wanted averages are needed by the task selection block and by
    the plots, so all of this is worked out before any of the html.
*/

$mtasks = filter_tasks($available_tasks, $models, $tasks, $mtasks, $types,
                       $langs, $srclangs, $trglangs);

$selected_tasks  = select_tasks($scores, $mtasks, $tasks, $langpairs);
$selected_models = get_selected_models($selected_tasks);

add_averages($scores, $selected_tasks, $available_tasks);

// a checkpoint of the bar chart is a training step, so keep these scores before
// the x axis below re-keys them to seconds or to consumed tokens
$barchart_scores = $scores;

// read token statistics if we want to plot scores per consumed tokens
if ($xaxis != 'training-steps'){
    foreach ($selected_models as $model){
        read_train_stats($traintoks, $traintime, $model, $selected_tasks, $available_tasks,
                         'train-progress.txt', $model_dir);
    }
    if ($xaxis == 'consumed-tokens'){
        $scores = score_per_trainbudget($scores, $traintoks);
    }
    elseif ($xaxis == 'training-time'){
        $scores = score_per_trainbudget($scores, $traintime);
    }
}

// the checkpoint list depends on the model, so drop it if it no longer fits
$barchartckpt = selected_checkpoint($barchart_scores, $barchart, $barchartidx, $barchartckpt);

// ------------------------------------------ filtering and model selection form

// number of filter groups that currently narrow the model list
$active_filters = count(array_filter(array_merge($model_components, $types, $langs, $langpairs)));
$filter_hint = count($filtered_models).' model'.(count($filtered_models) == 1 ? '' : 's')
              .($active_filters ? ', '.$active_filters.' filter'.($active_filters == 1 ? '' : 's') : '');
$selmodels_hint = count($models).' of '.count($filtered_models)
                 .' model'.(count($filtered_models) == 1 ? '' : 's');

echo('<form method="post">');
echo('<input type="hidden" id="showmodels" name="showmodels" value="'.$showmodels.'"/>');
echo('<input type="hidden" id="showselmodels" name="showselmodels" value="'.$showselmodels.'"/>');
echo('<input type="hidden" id="showtasks" name="showtasks" value="'.$showtasks.'"/>');
echo('<input type="hidden" name="selmodels_set" value="1"/>');
echo('<small>experiment directory: ');
experiments_form($available_expdirs, $expdir);
echo('</small><hr>');

// the filters, the model list and the task list are the tallest parts of the
// page, so all three are collapsible and each of them remembers its state
// across a reload
echo('<details class="modelselect" id="modelselect"'.($showmodels ? ' open' : '').'>');
echo('<summary>filtering models and tasks <span class="hint">('.$filter_hint.')</span></summary>');
echo('<table class="modelselect">');
model_components_form($available_models, $model_components);
if ($SHOW_SOURCELANG_SELECTION){
    language_checkbox_form('source languages', 'srclangs[]', $available_srclangs, $srclangs);
}
if ($SHOW_TARGETLANG_SELECTION){
    language_checkbox_form('target languages', 'trglangs[]', $available_trglangs, $trglangs);
}
if ($SHOW_LANGPAIR_SELECTION){
    language_form($available_srclangs, $available_trglangs, $langs);
}
task_form($available_tasktypes, $types);
echo('</table>');
echo('</details><hr/>');

// which of the filtered models go into the plots
echo('<details class="modelselect" id="modelsel"'.($showselmodels ? ' open' : '').'>');
echo('<summary>model selection <span class="hint">('.$selmodels_hint.')</span></summary>');
model_selection_form($filtered_models, $selmodels, $selmodels_set);
echo('</details><hr/>');

// which of the filtered tasks go into the plots
echo('<details class="modelselect" id="taskselect"'.($showtasks ? ' open' : '').'>');
echo('<summary>task selection</summary>');
task_selection_form($available_tasks, $tasks);
echo('</details><hr/>');

// the plot options follow the selection made in the blocks above, so they stay
// pinned to the top of the window while scrolling down through the plots; the
// page title is pinned with them, so it is always visible
echo('<div class="plotcontrols">');
echo('<h1>MAMMOTH Training Dashboard</h1>');
plot_graph_form($file, $xaxis);
barchart_form($barchart_scores, $barchart, $diff);
echo('</div>');

if (count($selected_tasks)){
    scores_plotly($scores, $selected_tasks, $xaxis, $metric);
}

// always called: whether the heading, the slider and the chart come out
// depends on whether there is anything to chart
scores_barchart($barchart_scores, $barchart, $metric, $barchartckpt, $file, $available_tasks, $diff);

echo('</form></body></html>');
