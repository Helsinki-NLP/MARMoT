<?php

/*
    MAMMOTH training dashboard - every function of the page, from reading the
    score files of the MARMoT repository over the selection and the forms to
    the plotly output. index.php includes this file and drives it; the
    constants MARMOT_GIT_RAW and SCORE_FILES it uses are defined there, and
    they have to be defined before one of these functions is called, not
    before they are declared.
*/

/*
    The label a score file is plotted under. Perplexity is also a log axis and
    sorted the other way round, which barchart_data() reads off this label.
*/

function metric_label($file){
    $labels = array('valid-scores-bleu.txt' => 'BLEU',
                    'valid-scores-chrf.txt' => 'ChrF',
                    'valid-scores-ppl.txt'  => 'perplexity');
    return isset($labels[$file]) ? $labels[$file] : 'BLEU';
}

// -----------------------------------------------------------------------
//  read score files from the GitHub repository
// -----------------------------------------------------------------------

/*
    Read the scores of one model from a csv file in the model directory.
    Fills $scores with $scores[$model][$task][$checkpoint] and collects the
    available tasks, task types and languages.
*/

function read_valid_scores(&$scores, &$tasks, &$srclangs, &$trglangs, &$types,
                           $model, $file, $dir='models'){

    $scores[$model] = array();

    // a model that was removed or never finished has no score file; that is
    // not an error here, so the warning is suppressed and checked for below
    $url = implode('/', array($dir, $model, 'stats', $file));
    $lines = @file($url);
    if ($lines === false) return;

    // the file starts with one or more "make" lines, then the checkpoint header
    $header = array_shift($lines);
    while ($header !== null && substr($header, 0, 4) == 'make'){
        $header = array_shift($lines);
    }
    if ($header === null) return;

    // skip the task and the gpu column
    $checkpoints = array_map('trim', array_slice(explode("\t", rtrim($header)), 2));

    foreach ($lines as $line) {
        if (substr($line, 0, 4) == 'make') continue;
        $line = rtrim($line);
        if ($line === '') continue;
        $parts = explode("\t", $line);
        array_shift($parts); // gpu column
        $task = array_shift($parts);
        $tasks[$task] = array_key_exists($task, $tasks) ? $tasks[$task]+1 : 1;
        $scores[$model][$task] = array();

        if (substr($task, 0, 7) != 'average'){
            list($type, $srclang, $trglang) = split_task_name($task);
            if ($type) $types[$type] = 1;
            if ($srclang && $trglang){
                $srclangs[$srclang] = 1;
                $trglangs[$trglang] = 1;
            }
        }

        foreach ($checkpoints as $checkpoint){
            $scores[$model][$task][$checkpoint] = array_shift($parts);
        }
    }
    ksort($scores); // sort the models so that the plots come in a stable order
}

/*
    Read the training statistics of one model (consumed tokens and wall-clock
    time per checkpoint) and average them over all/selected/available tasks.
*/

function read_train_stats(&$traintoks, &$traintime, $model, $selected_tasks,
                          $available_tasks, $file, $dir='models'){

    foreach (array('average-score','average-selected','average-filtered') as $bucket){
        $traintoks[$model][$bucket] = array();
        $traintime[$model][$bucket] = array();
    }

    $lines = file(implode('/',array($dir, $model, 'stats', $file)));
    if ($lines === false) return;

    $tokcount = 0;
    $taskcount = $selected_taskcount = $available_taskcount = 0;
    $restart_time = $lasttime = 0;

    foreach ($lines as $line) {
        if (substr($line, 0, 4) == 'make') continue;
        $line = rtrim($line);
        if ($line === '') continue;
        $parts = explode("\t", $line);
        // lines that are no score rows (e.g. sample predictions) have too few columns
        if (count($parts) < 8) continue;
        $taskparts = explode(': ', $parts[0]);
        if (count($taskparts) != 2) continue;
        $task = $taskparts[0];
        $step = $taskparts[1];
        $seconds = (int) str_replace(' sec', '', $parts[7]);
        list($toks) = explode(' ', trim($parts[5]));
        list($srctoks, $trgtoks) = explode('/', $toks);

        if (! array_key_exists($task, $traintoks[$model])){
            // a new task starts here, so restart the token counter
            $tokcount = 0;
            $lasttime = 0;
            $restart_time = 0;
            $taskcount++;
            if (in_array($model.':'.$task, $selected_tasks)) $selected_taskcount++;
            if (array_key_exists($task, $available_tasks)) $available_taskcount++;
        }

        // training runs may have been restarted, add the previous run's time
        if ($seconds + $restart_time < $lasttime){
            $restart_time = $lasttime;
        }
        $seconds += $restart_time;
        $diffsec = $seconds - $lasttime;
        $tokcount += $diffsec*((int)$srctoks + (int)$trgtoks);
        $lasttime = $seconds;

        $traintoks[$model][$task][$step] = $tokcount;
        $traintime[$model][$task][$step] = $seconds;

        // token budget averaged over all tasks
        accumulate_budget($traintoks, $traintime, $model, 'average-score', $step, $tokcount, $seconds);
        // ... over the selected tasks
        if (in_array($model.':'.$task, $selected_tasks)){
            accumulate_budget($traintoks, $traintime, $model, 'average-selected', $step, $tokcount, $seconds);
        }
        // ... over the tasks that pass the filters
        if (array_key_exists($task, $available_tasks)){
            accumulate_budget($traintoks, $traintime, $model, 'average-filtered', $step, $tokcount, $seconds);
        }
    }

    // divide the accumulated budgets by the number of averaged tasks
    $divisors = array('average-score'    => $taskcount,
                      'average-selected' => $selected_taskcount,
                      'average-filtered' => $available_taskcount);
    foreach ($divisors as $bucket => $nr){
        if (! $nr) continue;
        foreach ($traintoks[$model][$bucket] as $step => $count){
            $traintoks[$model][$bucket][$step] = $count/$nr;
            $traintime[$model][$bucket][$step] /= $nr;
        }
    }
}

// add a token/time budget to the running sum of one of the average buckets
function accumulate_budget(&$traintoks, &$traintime, $model, $bucket, $step, $tokcount, $seconds){
    if (array_key_exists($step, $traintoks[$model][$bucket])){
        $traintoks[$model][$bucket][$step] += $tokcount;
        $traintime[$model][$bucket][$step] += $seconds;
    }
    else{
        $traintoks[$model][$bucket][$step] = $tokcount;
        $traintime[$model][$bucket][$step] = $seconds;
    }
}

/*
    Add average scores where they are needed:
    - average-filtered: average over all tasks that pass the filters
    - average-selected: average over the selected tasks
*/

function add_averages(&$scores, $selected_tasks, $available_tasks){
    foreach ($scores as $model => $tasks){
        if (wants_average($model, 'average-filtered', $selected_tasks)){
            $series = array();
            foreach ($available_tasks as $task => $count){
                if (substr($task, 0, 7) == 'average') continue;
                if (array_key_exists($task, $tasks)) $series[] = $tasks[$task];
            }
            $scores[$model]['average-filtered'] = average_series($series);
        }
        if (wants_average($model, 'average-selected', $selected_tasks)){
            $series = array();
            foreach ($selected_tasks as $selected_task){
                $taskparts = explode(':', $selected_task);
                $task = array_pop($taskparts);
                if (substr($task, 0, 7) == 'average') continue;
                if (array_key_exists($task, $tasks)) $series[] = $tasks[$task];
            }
            $scores[$model]['average-selected'] = average_series($series);
        }
    }
}

// is an average score requested for this model?
function wants_average($model, $kind, $selected_tasks){
    return in_array($kind, $selected_tasks) || in_array($model.':'.$kind, $selected_tasks);
}

// average a list of score series over all checkpoints they have in common
function average_series($series_list){
    $sums = array();
    $counts = array();
    foreach ($series_list as $series){
        foreach ($series as $step => $score){
            $sums[$step] = array_key_exists($step, $sums) ? $sums[$step]+$score : $score;
            $counts[$step] = array_key_exists($step, $counts) ? $counts[$step]+1 : 1;
        }
    }
    foreach ($sums as $step => $sum){
        $sums[$step] = $sum/$counts[$step];
    }
    return $sums;
}

/*
    Split task names into components
    - assumes a format like type_srclang-trglang
    - entries that start with 'average' are average scores, not tasks
*/

function split_task_name($task){
    if (substr($task, 0, 7) == 'average'){
        return array(null, null, null);
    }
    $langs = explode('-', $task);
    $lang1parts = explode('_', $langs[0]);
    $srclang = null;
    $trglang = null;
    if (count($langs) == 2){
        $srclang = count($lang1parts) > 1 ? $lang1parts[1] : $langs[0];
        $trglang = $langs[1];
    }
    return array($lang1parts[0], $srclang, $trglang);
}

// the name of a model, i.e. "base-1p+d-Genc-Ldec/mammoth" -> "base-1p+d-Genc-Ldec"
function model_name($model){
    list($name) = explode('/', rtrim($model));
    return $name;
}

// -----------------------------------------------------------------------
//  model and task selection
// -----------------------------------------------------------------------

/*
    Keep only the models whose name components match all component filters
    and add them to $selected_models.
*/

function select_models(&$models, &$selected_models, &$selected_model_components){
    foreach ($models as $m){
        $m = rtrim($m);
        $components = explode('-', model_name($m));
        $model_ok = true;
        for ($i = 0; $i < count($selected_model_components); $i++){
            if (! count($selected_model_components[$i])) continue;
            if (! isset($components[$i]) || ! in_array($components[$i], $selected_model_components[$i])){
                $model_ok = false;
                break;
            }
        }
        if ($model_ok){
            $selected_models[] = $m;
        }
    }
    $selected_models = array_unique($selected_models);
}

/*
    Filter the available tasks according to the selected criteria and return
    the selected model/task combinations ("model:task") that survive.
*/

function filter_tasks(&$available_tasks, $selected_models, $selected_tasks, $selected_mtasks,
                      $selected_tasktypes, $selected_langs, $selected_srclangs, $selected_trglangs){

    // only keep tasks that are available for all selected models
    $nr_of_models = count($selected_models);
    foreach ($available_tasks as $task => $count){
        if ($count < $nr_of_models){
            unset($available_tasks[$task]);
        }
    }

    // keep the tasks that pass all filters
    $filtered_tasks = array();
    foreach ($available_tasks as $task => $nr){
        list($type, $srclang, $trglang) = split_task_name($task);

        if ($type && $selected_tasktypes && ! in_array($type, $selected_tasktypes)) continue;
        if ($srclang && $trglang && $selected_langs
            && ! in_array($srclang, $selected_langs) && ! in_array($trglang, $selected_langs)) continue;
        if ($srclang && $selected_srclangs && ! in_array($srclang, $selected_srclangs)) continue;
        if ($trglang && $selected_trglangs && ! in_array($trglang, $selected_trglangs)) continue;

        $filtered_tasks[$task] = $nr;
    }
    $available_tasks = $filtered_tasks;

    // collect the tasks that are still available, or the requested averages
    $tasks = array();
    foreach ($selected_mtasks as $task){
        $parts = explode(':', $task);
        if (count($parts) < 2) continue;
        list($model, $taskname) = $parts;
        if (array_key_exists($taskname, $available_tasks) || substr($taskname, 0, 7) == 'average'){
            $tasks[] = $task;
        }
    }
    foreach ($selected_tasks as $task){
        if (array_key_exists($task, $available_tasks)){
            $tasks[] = $task;
        }
    }
    return $tasks;
}

/*
    Turn the selected model/task combinations into a list of score series to
    plot ("model:task" or "model:average-*").
*/

function select_tasks($scores, $selected_mtasks, $selected_tasks, $selected_langpairs){
    $selected = $selected_mtasks;

    foreach ($scores as $model => $tasks){
        foreach (array('average-filtered', 'average-selected') as $average){
            if (in_array($average, $selected_tasks)){
                $selected[] = $model.':'.$average;
            }
        }
        foreach ($tasks as $task => $score){
            if (in_array($model.':'.$task, $selected_mtasks)) continue;
            if (in_array($task, $selected_tasks)){
                $selected[] = $model.':'.$task;
                continue;
            }
            list($type, $srclang, $trglang) = split_task_name($task);
            if ($srclang && $trglang && in_array($srclang.'-'.$trglang, $selected_langpairs)){
                $selected[] = $model.':'.$task;
            }
        }
    }
    return $selected;
}

// the models that occur in the given list of "model:task" combinations
function get_selected_models($selected_tasks){
    $models = array();
    foreach ($selected_tasks as $task){
        $parts = explode(':', $task);
        if (count($parts) > 1){
            $models[$parts[0]] = 1;
        }
    }
    return array_keys($models);
}

// replace the checkpoint axis of the scores with a token/time budget axis
function score_per_trainbudget($scores, $trainbudget){
    $scores_per_budget = array();
    foreach ($scores as $model => $tasks){
        foreach ($tasks as $task => $checkpoints){
            foreach ($checkpoints as $checkpoint => $score){
                if (! isset($trainbudget[$model][$task][$checkpoint])) continue;
                $budget = (int) $trainbudget[$model][$task][$checkpoint];
                $scores_per_budget[$model][$task][$budget] = $score;
            }
        }
    }
    return $scores_per_budget;
}


// -----------------------------------------------------------------------
//  forms
// -----------------------------------------------------------------------

function checkbox($name, $value, $label, $checked){
    return "<input type='checkbox' name='".htmlspecialchars($name)."' value='".htmlspecialchars($value)."'"
        .($checked ? " checked='checked'" : '').">&nbsp;".htmlspecialchars($label);
}

function radio($id, $name, $value, $label, $checked){
    return "<input type='radio' id='".htmlspecialchars($id)."' name='".htmlspecialchars($name)."'"
        ." value='".htmlspecialchars($value)."'"
        .($checked ? " checked='checked'" : '')."><label for='".htmlspecialchars($id)."'>"
        .htmlspecialchars($label).'</label> ';
}

function experiments_form($available_expdirs, $selected_expdir){
    foreach ($available_expdirs as $expdir){
        $exp = rtrim($expdir);
        echo(radio($exp, 'expdir', $exp, $exp, $selected_expdir == $exp));
    }
}

// one line of checkboxes for a single list of languages
function language_checkbox_form($label, $param, $available_langs, $selected_langs){
    ksort($available_langs);
    echo("<tr><td class='modelselect_col1'>$label: </td><td>");
    $count = 0;
    foreach ($available_langs as $lang => $nr){
        echo(checkbox($param, $lang, $lang, in_array($lang, $selected_langs)));
        if ((++$count % 15) == 0) echo '<br/>';
    }
    echo('</td></tr><tr>');
}

// checkboxes for the languages, whether they are source or target languages
function language_form(&$available_srclangs, &$available_trglangs, &$selected_langs){
    $available_langs = array_merge($available_srclangs, $available_trglangs);
    ksort($available_langs);
    echo("<tr><td class='modelselect_col1'>language:<br/>(source or target) </td>");
    echo('<td><table class="langselect"><tr>');
    $count = 0;
    foreach ($available_langs as $lang => $nr){
        echo('<td class="dense">'.checkbox('langs[]', $lang, $lang, in_array($lang, $selected_langs)).'</td>');
        if ((++$count % 15) == 0) echo '</tr><tr>';
    }
    echo('</tr></table></td></tr><tr>');
}

function task_form(&$available_tasktypes, &$selected_tasktypes){
    echo("<tr><td class='modelselect_col1'>task types: </td><td>");
    foreach ($available_tasktypes as $tasktype => $nr){
        echo(checkbox('tasktypes[]', $tasktype, $tasktype, in_array($tasktype, $selected_tasktypes)));
    }
    echo('</td></tr>');
}

/*
    A checkbox for every component of the model names (e.g. "1p", "+d",
    "Genc-Ldec", "320k"), so that models can be filtered by component.
*/

function model_components_form(&$models, &$selected_model_components){
    $model_components = array();
    foreach ($models as $m){
        $components = explode('-', model_name($m));
        foreach ($components as $i => $component){
            $model_components[$i][$component] = 1;
        }
    }

    foreach ($model_components as $i => $components){
        if (! isset($selected_model_components[$i])) $selected_model_components[$i] = array();
        echo("<tr><td class='modelselect_col1'>component $i:</td><td>");
        $param = 'mcomp'.$i.'[]';
        $count = 0;
        foreach ($components as $component => $nr){
            echo(checkbox($param, $component, $component, in_array($component, $selected_model_components[$i])));
            if ((++$count % 10) == 0) echo '<br/>';
        }
        echo('</td></tr>');
    }
}

/*
    A checkbox for every model the filters let through, laid out in columns of
    fifteen like the model list used to be. Every model is checked until the
    block is submitted for the first time; from then on the checkboxes say
    which models go into the plots.
*/

function model_selection_form(&$models, $selected, $has_selection){
    if (! count($models)){
        echo('<p class="hint">the filters let no model through</p>');
        return;
    }

    echo('<table class="modelselect"><tr>');
    echo("<td class='modelselect_list'>");
    $count = 0;
    foreach ($models as $model){
        $checked = ! $has_selection || in_array($model, $selected);
        echo('<label>'.checkbox('selmodels[]', $model, model_name($model), $checked).'</label><br/>');
        if ((++$count % 15) == 0) echo "</td><td class='modelselect_list'>";
    }
    echo('</td></tr></table>');
    echo('<p><button type="button" onclick="setModelSelection(true);">select all</button> ');
    echo('<button type="button" onclick="setModelSelection(false);">select none</button></p>');
}

function task_selection_form($available_tasks, &$selected_tasks){
    echo('<table class="modelselect"><tr>');
    ksort($available_tasks);
    $count = 0;
    foreach ($available_tasks as $task => $nr){
        // the average over the selection is no longer offered; an old link
        // that still submits it is honoured all the same
        if ($task == 'average-selected') continue;
        echo('<td class="dense">'.checkbox('tasks[]', $task, $task, in_array($task, $selected_tasks)).'</td>');
        if ((++$count % 10) == 0) echo '</tr><tr>';
    }
    echo('</tr></table>');
}

function plot_graph_form($file, $xaxis){
    echo('<p><input type="submit" name="submit" value="plot graph" />');
    echo('<button type="button" onclick="resetSelected();">reset</button> ');
    echo('<input type="hidden" name="file" value="'.htmlspecialchars($file).'" />');

    echo(radio('valid-scores-bleu', 'file', 'valid-scores-bleu.txt', 'BLEU', $file == 'valid-scores-bleu.txt'));
    echo(radio('valid-scores-chrf', 'file', 'valid-scores-chrf.txt', 'ChrF', $file == 'valid-scores-chrf.txt'));
    echo(radio('valid-scores-ppl', 'file', 'valid-scores-ppl.txt', 'perplexity', $file == 'valid-scores-ppl.txt'));

    echo(radio('xaxis-training-steps', 'xaxis', 'training-steps', 'iterations', $xaxis == 'training-steps'));
    echo(radio('xaxis-training-time', 'xaxis', 'training-time', 'time', $xaxis == 'training-time'));
    echo(radio('xaxis-consumed-tokens', 'xaxis', 'consumed-tokens', 'token budget', $xaxis == 'consumed-tokens'));

    echo('</p>');
}

/*
    The controls of the bar chart: the model whose tasks are shown, the diff
    option next to it, and the checkpoint the bars are taken from. The model
    list only contains the models whose scores are already loaded, so no extra
    files are fetched. The checkpoint is a slider rather than a drop-down,
    because the steps are evenly spaced and there can be dozens of them. The
    slider submits its position, not the checkpoint, and moving it redraws the
    chart in place through javascript. The checkpoint list follows the model,
    so switching model still needs "plot graph".
*/

function barchart_form($scores, $selected_barchart, $diff){
    echo('<p><label for="barchart">bar chart for model: </label>');
    echo('<select id="barchart" name="barchart">');
    echo('<option value=""'.($selected_barchart ? '' : ' selected').'>(none)</option>');
    // every selected model at once, as one group of bars per task; there is
    // nothing to chart that way while no model is selected
    if (count($scores)){
        echo('<option value="'.BARCHART_ALL.'"'
            .($selected_barchart === BARCHART_ALL ? ' selected' : '')
            .'>all selected models</option>');
    }
    foreach (array_keys($scores) as $model){
        echo('<option value="'.htmlspecialchars($model).'"'
            .($model == $selected_barchart ? ' selected' : '').'>'
            .htmlspecialchars(model_name($model)).'</option>');
    }
    echo('</select>');
    // the bars are either the score itself or its diff against the previous
    // checkpoint, which is what this switches
    echo(' '.checkbox('diff', '1', 'diff', $diff));

    if (! count($scores)){
        echo(' <small>(select models first)</small>');
    }
    else{
        echo(' <span id="barStatus" class="hint">'
             .($selected_barchart ? 'loading...' : '').'</span>');
    }
}

/*
    All checkpoints that the tasks of a model have scores for, in ascending
    order. Falls back to the checkpoints of all loaded models as long as no
    bar chart model has been selected, which is also the union the "(all)"
    choice is charted against.
*/

function model_checkpoints($scores, $model){
    if ($model && ! isset($scores[$model])) $model = '';   // stale, forged or "(all)"
    $models = $model ? array($model) : array_keys($scores);

    $checkpoints = array();
    foreach ($models as $m){
        foreach ($scores[$m] as $task => $values){
            if (substr($task, 0, 7) == 'average') continue;
            foreach (array_keys($values) as $checkpoint) $checkpoints[$checkpoint] = 1;
        }
    }
    $checkpoints = array_keys($checkpoints);
    sort($checkpoints, SORT_NUMERIC);
    return $checkpoints;
}

/*
    Which checkpoint the bar chart shows.

    The slider submits its position rather than a checkpoint, because a
    checkpoint name is a long number and positions are what a slider can
    step through. Position 0 is "last", position n is the n-th checkpoint.
    Older links submit the checkpoint itself, which is still accepted.
    Anything out of range becomes "last", so that the form, the plot title
    and the bars can never disagree.

    The comparison against the checkpoint list is deliberately loose: the
    checkpoints are array keys, so php stores them as integers while the
    form and old links submit them as strings.
*/

function selected_checkpoint($scores, $model, $position, $name){
    $checkpoints = model_checkpoints($scores, $model);
    if ($position !== '' && $position !== null && ctype_digit((string) $position)){
        $position = (int) $position;
        if ($position > 0 && $position <= count($checkpoints)){
            return (string) $checkpoints[$position-1];
        }
        return 'last';
    }
    if ($name != 'last' && in_array($name, $checkpoints)){
        return $name;
    }
    return 'last';
}

/*
    Where a checkpoint sits on the slider: 0 for "last", otherwise its
    one-based position in the model's checkpoint list.
*/

function checkpoint_position($checkpoints, $ckpt){
    if ($ckpt != 'last'){
        $position = array_search($ckpt, $checkpoints);
        if ($position !== false) return $position + 1;
    }
    return 0;
}

// -----------------------------------------------------------------------
//  plotting
// -----------------------------------------------------------------------

// load plotly.js, at most once per page
function plotly_js(){
    static $loaded = false;
    if ($loaded) return;
    $loaded = true;
    echo('<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>');
}

// plot one line per selected model/task combination
function scores_plotly($scores, $selected, $xlabel, $ylabel='BLEU'){
    // the traces are built first, so that a selection which turns out to hold
    // no scores at all does not leave an empty frame of axes behind
    $traces = array();
    foreach ($selected as $sel){
        $parts = explode(':', $sel);
        if (count($parts) < 2) continue;
        list($model, $task) = $parts;
        if (! $model || ! $task) continue;
        if (! isset($scores[$model][$task])) continue;
        if (! count($scores[$model][$task])) continue;
        $traces[] = "{ x: [".implode(', ', array_keys($scores[$model][$task]))."], y: ["
            .implode(', ', array_values($scores[$model][$task]))."], mode: 'lines+markers', name: "
            .json_encode($task.'/'.model_name($model), JSON_UNESCAPED_SLASHES)." },";
    }
    if (! count($traces)) return;          // nothing to plot: not even a frame

    echo('</pre>');
    plotly_js();
    echo('<div id="myPlot" style="width:200%;max-width:960px;max-height:400px"></div><script>');

    echo("\nconst data = [\n");
    foreach ($traces as $trace) echo($trace."\n");
    echo("];\n");

    $layout = array(
        'showlegend' => true,
        'xaxis' => array('title' => $xlabel),
        'yaxis' => $ylabel == 'perplexity'
            ? array('title' => $ylabel, 'type' => 'log')
            : array('title' => $ylabel),
        'margin' => array('l' => 50, 'r' => 150, 'b' => 100, 't' => 10, 'pad' => 4),
    );
    echo('const layout = '.json_encode($layout).";\n");
    echo('Plotly.newPlot("myPlot", data, layout);');
    echo('</script>');
}

/*
    Validation score of every task of one model as a bar chart. The height of a
    bar is the score of that task at the selected checkpoint, or at its own
    last checkpoint if the task does not reach that far; tasks are ordered
    best-first and coloured by task type, so that the strengths and weaknesses
    of a model are visible at a glance.

    All scores of all checkpoints are handed to the browser as BAR_DATA, and
    the chart itself is drawn by drawBarChart(). Switching the checkpoint then
    only re-sorts and re-draws, without another request to github.
*/

function scores_barchart($scores, $model, $ylabel='BLEU', $ckpt='last', $file='',
                         $allowed_tasks=null, $diff=false){
    if ($model === BARCHART_ALL){
        $data = barchart_data_all($scores, $ylabel, $ckpt, $allowed_tasks);
    }
    elseif ($model && isset($scores[$model])){
        $data = barchart_data($scores, $model, $ylabel, $ckpt, $allowed_tasks);
    }
    else{
        $data = null;
    }

    plotly_js();
    // the score file is always handed over: it is what a model chosen later in
    // the drop-down is read for, and that has to be the metric this page shows;
    // the task list the filters left is handed over as well, so that the scores
    // fetched for another model are cut down to the same tasks
    echo('<script>BAR_FILE = '.json_encode($file).";</script>\n");
    echo('<script>BAR_TASKS = '
        .json_encode($allowed_tasks === null ? null : array_keys($allowed_tasks)).";</script>\n");
    // the diff option is a display choice of this page, so only the flag is
    // handed over: the differences themselves are worked out in the browser
    // from the checkpoint scores the payload carries anyway, which keeps the
    // json endpoint free of the option
    echo('<script>BAR_DIFF = '.($diff ? 'true' : 'false').";</script>\n");

    // the heading and the slider belong to a chart that is actually there:
    // without one they stay out of sight, and javascript brings them back when
    // a model is chosen in the drop-down. The plot div is always in the page,
    // so that a model picked later has somewhere to draw into
    $shown = ($data !== null);
    echo('<div id="barhead"'.($shown ? '' : ' hidden').">\n");
    echo('<h2>Validation scores per task</h2>');
    barchart_slider($shown ? $data['checkpoints'] : array(), $ckpt, $shown);
    echo("</div>\n");
    echo('<div id="barPlot"'.($shown ? '' : ' class="empty"').'></div>');

    if (! $shown){
        // a chosen model without anything to show says so, rather than leaving
        // the "loading ..." of the form standing
        if ($model){
            if ($model === BARCHART_ALL){
                $status = count($scores)
                        ? 'no task is left by the filters'
                        : 'no model is selected any more';
            }
            elseif (isset($scores[$model])){
                $status = 'no task of '.model_name($model).' is left by the filters';
            }
            else{
                $status = model_name($model).' is not selected any more';
            }
            echo('<script>barChartStatus('.json_encode($status).');</script>');
        }
        return;
    }

    echo("<script>\nBAR_DATA = ".json_encode($data, JSON_UNESCAPED_SLASHES).";\n");
    echo('drawBarChart(BAR_DATA.selected);</script>');
}

/*
    The checkpoint slider, placed with the chart it drives rather than with the
    other plot options, so that it is where the reader is looking. Position 0
    is "last", position n is the n-th checkpoint; moving it redraws the chart
    through javascript, so it only has to be submitted to survive a reload.
*/

function barchart_slider($checkpoints, $ckpt, $enabled){
    $checkpoints = array_map('strval', $checkpoints);
    $name = htmlspecialchars($ckpt);
    echo('<p><label for="barchartckpt">at checkpoint: </label>');
    echo('<input type="range" id="barchartckpt" name="barchartidx"'
        .' min="0" max="'.count($checkpoints).'" step="1"'
        .' value="'.checkpoint_position($checkpoints, $ckpt).'"'
        .' aria-label="checkpoint" aria-valuetext="'.$name.'"'
        .($enabled ? '' : ' disabled').'/>');
    echo('<output id="barchartckptval" for="barchartckpt">'.$name.'</output>');
    if ($enabled){
        echo(' <span class="hint">drag to move through the checkpoints</span>');
    }
    echo('</p>');
}

/*
    The validation scores of one model as the browser needs them: every task of
    the model against every checkpoint it has scores for. This is the single
    place that builds that payload, so that the version embedded in the page
    and the one the browser fetches for another model cannot drift apart.

    $allowed_tasks are the tasks the filters left, i.e. the same list the task
    checkboxes below the plots are rendered from; only those tasks end up in
    the payload. It is null for a raw fetch, which lets the browser fetch every
    task of a model and do the cutting down itself (filterBarTasks).

    Returns null when the model has no tasks to show.
*/

function barchart_data($scores, $model, $ylabel='BLEU', $ckpt='last', $allowed_tasks=null){
    // the real tasks of the model, ignoring the computed averages, and only
    // those the filters let through
    $tasks = array();
    foreach ($scores[$model] as $task => $checkpoints){
        if (substr($task, 0, 7) == 'average') continue;
        if ($allowed_tasks !== null && ! isset($allowed_tasks[$task])) continue;
        if (count($checkpoints)) $tasks[] = $task;
    }
    if (! count($tasks)) return null;

    $available = model_checkpoints($scores, $model);

    // one colour per task type
    $palette = array();
    $colors = array();
    foreach ($tasks as $i => $task){
        list($type) = split_task_name($task);
        if (! array_key_exists($type, $palette)) $palette[$type] = plotly_color(count($palette));
        $colors[$i] = $palette[$type];
    }

    // scores[task index] at every checkpoint, null where a task has none
    $matrix = array();
    foreach ($available as $checkpoint){
        $row = array();
        foreach ($tasks as $i => $task){
            $score = isset($scores[$model][$task][$checkpoint])
                     ? $scores[$model][$task][$checkpoint] : null;
            $row[$i] = is_numeric($score) ? (float) $score : null;
        }
        $matrix[(string) $checkpoint] = $row;
    }

    // each task's own final score, used for "last" and for tasks that do not
    // reach the requested checkpoint
    $last = array();
    $last_at = array();
    foreach ($tasks as $i => $task){
        $keys = array_keys($scores[$model][$task]);
        $at = (string) end($keys);   // keys are ints in php, the form sends strings
        $score = $scores[$model][$task][$at];
        $last[$i] = is_numeric($score) ? (float) $score : null;
        $last_at[$i] = $at;
    }

    $data = array(
        'metric'      => $ylabel,
        'descending'  => $ylabel != 'perplexity',  // perplexity: lower is better
        'log'         => $ylabel == 'perplexity',
        'model'       => model_name($model),
        'checkpoints' => array_map('strval', $available),
        'tasks'       => $tasks,
        'colors'      => $colors,
        'scores'      => $matrix,
        'last'        => $last,
        'lastAt'      => $last_at,
        'selected'    => $ckpt,
    );

    return $data;
}

/*
    The scores of every model in $scores as the browser needs them for the
    "all selected models" choice of the drop-down: one group of bars per task,
    sorted by task, with one bar per model in it.

    Only tasks every model has scores for end up in the payload, so the bars
    of the models line up task by task; everything else follows
    barchart_data(), including the null for a model that does not reach a
    checkpoint. Returns null when there is nothing to show.
*/

function barchart_data_all($scores, $ylabel='BLEU', $ckpt='last', $allowed_tasks=null){
    if (! count($scores)) return null;

    // the tasks that all models have scores for, kept in task order
    $tasks = null;
    foreach ($scores as $model => $by_task){
        $have = array();
        foreach ($by_task as $task => $checkpoints){
            if (substr($task, 0, 7) == 'average') continue;
            if ($allowed_tasks !== null && ! isset($allowed_tasks[$task])) continue;
            if (count($checkpoints)) $have[$task] = true;
        }
        $tasks = ($tasks === null) ? $have : array_intersect_key($tasks, $have);
    }
    if ($tasks === null || ! count($tasks)) return null;
    $tasks = array_keys($tasks);
    sort($tasks);

    $models = array_keys($scores);

    // the union of the models' checkpoints, ascending: the same list the
    // slider of this page steps through, because model_checkpoints() also
    // falls back to every loaded model for the "(all)" choice
    $available = model_checkpoints($scores, '');

    // scores[checkpoint][model index][task index], null where a model has none
    $matrix = array();
    foreach ($available as $checkpoint){
        $row = array();
        foreach ($models as $mi => $model){
            foreach ($tasks as $ti => $task){
                $score = isset($scores[$model][$task][$checkpoint])
                       ? $scores[$model][$task][$checkpoint] : null;
                $row[$mi][$ti] = is_numeric($score) ? (float) $score : null;
            }
        }
        $matrix[(string) $checkpoint] = $row;
    }

    // every model's own final score per task, for the same two purposes
    // barchart_data() keeps it: "last" and tasks that reach no checkpoint
    $last = array();
    $last_at = array();
    foreach ($models as $mi => $model){
        foreach ($tasks as $ti => $task){
            $keys = array_keys($scores[$model][$task]);
            $at = (string) end($keys);   // keys are ints in php, the form sends strings
            $score = $scores[$model][$task][$at];
            $last[$mi][$ti] = is_numeric($score) ? (float) $score : null;
            $last_at[$mi][$ti] = $at;
        }
    }

    // one colour per model, so the bars of a model stay tellable apart
    $colors = array();
    foreach ($models as $mi => $model) $colors[$mi] = plotly_color($mi);

    return array(
        'metric'      => $ylabel,
        'descending'  => $ylabel != 'perplexity',  // perplexity: lower is better
        'log'         => $ylabel == 'perplexity',
        'all'         => true,
        'model'       => 'all selected models',
        'models'      => array_map('model_name', $models),
        'modelColors' => $colors,
        'checkpoints' => array_map('strval', $available),
        'tasks'       => $tasks,
        'scores'      => $matrix,
        'last'        => $last,
        'lastAt'      => $last_at,
        'selected'    => $ckpt,
    );
}

/*
    Answer a bar chart model swap with the scores of that one model as json.

    This runs before the page is built, so it works out for itself what the
    request is asking for: the experiment directory and the score file are read
    from the query string, validated against the same rules the page uses, and
    everything else about the request is ignored.

    The model has to be one the experiment directory lists and the score file
    has to be one of the three known ones. Both names end up in the path of a
    file to read, so without that check they would be a way of reading any file
    of the repository.
*/

function barchart_json_response(){
    $raw       = MARMOT_GIT_RAW;
    $expdir    = get_param('expdir', 'hpo');
    $model_dir = $raw.'/models/'.$expdir;
    $file      = get_param('file', SCORE_FILES[0]);

    // the same restriction the page applies to the score file it reads
    if (! in_array($file, SCORE_FILES)) $file = SCORE_FILES[0];

    $available_models = @file($model_dir.'/models.txt');
    if ($available_models === false) $available_models = array();

    $known = array();
    foreach ($available_models as $m){
        $m = rtrim($m);
        if ($m !== '') $known[$m] = true;
    }

    header('Content-Type: application/json');

    $model = get_param('barchartdata', '');
    if ($model === '' || ! isset($known[$model])){
        header('HTTP/1.1 400 Bad Request');
        echo json_encode(array('error' => 'unknown model')), "\n";
        return;
    }

    // only this one model is read, which is what keeps the request quick
    $scores = $tasks = $srclangs = $trglangs = $types = array();
    read_valid_scores($scores, $tasks, $srclangs, $trglangs, $types,
                      $model, $file, $model_dir);

    $data = barchart_data($scores, $model, metric_label($file), 'last');
    if ($data === null){
        header('HTTP/1.1 404 Not Found');
        echo json_encode(array('error' => 'model has no scores')), "\n";
        return;
    }
    echo json_encode($data, JSON_UNESCAPED_SLASHES), "\n";
}

// a colour-blind friendly palette, wrapping around when it runs out
function plotly_color($i){
    $palette = array('31,119,180', '255,127,14', '44,160,44', '214,39,40',
                     '148,103,189', '140,86,75', '227,119,194', '127,127,127');
    return 'rgb('.$palette[$i % count($palette)].')';
}


// -----------------------------------------------------------------------
//  CGI argument handling
// -----------------------------------------------------------------------

function get_param($key, $default){
    if (! isset($_REQUEST[$key])) return $default;
    // note: without session_start() this is a plain array, i.e. not persisted
    $_SESSION['params'][$key] = test_input($_REQUEST[$key]);
    return $_SESSION['params'][$key];
}

/*
    A parameter that the form submits as name[]=value. Always returns an array,
    so a hand-crafted request such as "?models=foo" cannot break the page.
*/

function get_array_param($key){
    $value = get_param($key, array());
    return is_array($value) ? $value : array($value);
}

// escape everything that is echoed back into the html
function test_input($data) {
    if (! is_array($data)){
        $data = trim($data);
        $data = stripslashes($data);
        $data = htmlspecialchars($data);
    }
    return $data;
}