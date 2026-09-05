<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">

<html>
<head>
  <title>MAMMOTH Training Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
<script>
function resetSelected() {
  var inputs=document.getElementsByTagName("input");
  for (var i in inputs)
      if (inputs[i].type=="checkbox") inputs[i].checked=false;
}
</script>
<?php

if (isset($_POST['submit'])){
    if ($_POST['submit']=='reset'){
        // session_destroy();
        $_POST = array();
        $_REQUEST = array();
        $_SESSION = array();
    }
}
// session_start();


# $MarmotGitRaw = 'https://raw.githubusercontent.com/Helsinki-NLP/MARMoT/refs/heads/lumi';
# $model_dir = $MarmotGitRaw.'/models';
$MarmotGitRaw = 'https://raw.githubusercontent.com/Helsinki-NLP/MARMoT/refs/heads/main';
$model_dir = $MarmotGitRaw.'/models/pytorch';

# $available_models = file($MarmotGitRaw.'/models/models.txt');
$available_models = file($MarmotGitRaw.'/models/pytorch/models.txt');

$models    = get_param('models', array());
$features  = get_param('features', array());
$file      = get_param('file', 'valid-scores-bleu.txt');
$tasks     = get_param('tasks', array());
$types     = get_param('tasktypes', array());
$srclangs  = get_param('srclangs', array());
$trglangs  = get_param('trglangs', array());
$langpairs = get_param('langpairs', array());
$xaxis     = get_param('xaxis', 'training-steps');

// var_dump($srclangs);

if ($file == 'valid-scores-bleu.txt') $metric = 'BLEU';
elseif ($file == 'valid-scores-chrf.txt') $metric = 'ChrF';
else $metric = 'perplexity';


echo('<form method="post">');
echo('<small><table>');
// select_models($available_models, $models);
select_model_features($available_models, $models, $features);

$scores = array();
$traintoks = array();
$available_tasks = array('averageavailable' => 1, 'averageselected' => 1);
$available_tasktypes = array();
$available_srclangs = array();
$available_trglangs = array();
$available_langpairs = array();

foreach ($models as $m){
    read_valid_scores($scores,
                      $available_tasks,
                      $available_srclangs,
                      $available_trglangs,
                      $available_langpairs,
                      $available_tasktypes,
                      rtrim($m), $file, $model_dir);
    if ($xaxis == "consumed-tokens"){
        read_train_stats($traintoks,rtrim($m),'train-progress.txt', $model_dir);
    }
}

// echo('<br/>');

$tasks = filter_tasks($available_tasks,
                      $available_srclangs,
                      $available_trglangs,
                      $available_langpairs,
                      $available_tasktypes,
                      $tasks,
                      $srclangs,$trglangs,
                      $langpairs,
                      $types);

echo('<tr><td></td><td><input type="submit" name="submit" value="select" />');
echo('<button type="button" onclick="resetSelected();">reset</button></td></tr>');
echo('</table></small><hr/>');



echo("<h1>MAMMOTH Training Dashboard</h1>");



$selected = select_tasks($scores, $tasks, $types, $langpairs);
add_averages($scores, $selected, $available_tasks, $metric);
if ($xaxis == "consumed-tokens"){
    $scores = score_per_tokenbudget($scores,$traintoks);
}

scores_plotly($scores, $selected, $xaxis, $metric);

model_tasks($available_models, $available_tasks, $available_langpairs, $scores, $models, $tasks, $types, $langpairs, $file);
echo('</form></body></html>');
    


function get_models($dir='models'){
    $models = array();
    if ($handle = opendir($dir)) {
        while (false !== ($entry = readdir($handle))) {
            if ($entry != "." && $entry != "..") {
                if (is_dir("models/$entry")){
                    array_push($models,$entry);
                }
            }
        }
        closedir($handle);
    }
    rsort($models);
    return $models;
}


function select_tasks(&$scores, &$selected_tasks, &$selected_types, &$selected_langpairs){
    $selected = $selected_tasks;
    $models = array();

    foreach ($scores as $model => $tasks){
        $models[$model] = 1;
        foreach ($tasks as $task => $score){
            if (! in_array($model.':'.$task, $selected_tasks)){
                list($type,$srclang,$trglang) = split_task_name($task);
                $langpair = implode('-',array($srclang,$trglang));
                if (in_array($langpair, $selected_langpairs)){
                    array_push($selected,$model.':'.$task);
                }
            }
        }
    }
    return $selected;
}



/*
add average scores if necessary:
- average over all available tasks (after filtering with languages and types)
- average over all selected tasks
*/

function add_averages(&$scores,&$selected_tasks,&$available_tasks,$metric){
    foreach ($scores as $model => $tasks){
        $modeltask = $model.':averageavailable';
        if (in_array('averageavailable',$selected_tasks) or
            in_array($model.':averageavailable',$selected_tasks) or
            array_key_exists($model.':averageavailable',$available_tasks)){
            $avgscores = array();
            $counts = array();
            foreach ($available_tasks as $available_task => $idx){
                if (substr($available_task,0,7) == 'average') continue;
                if (array_key_exists($available_task,$tasks)){
                    foreach ($tasks[$available_task] as $step => $score){
                        if (! array_key_exists($step,$avgscores)){
                            $avgscores[$step] = $score;
                            $counts[$step] = 1;
                        }
                        else{
                            $avgscores[$step] += $score;
                            $counts[$step]++;
                        }
                    }
                }
            }
            foreach ($avgscores as $step => $score){
                if ($counts[$step]){
                    $avgscores[$step] /= $counts[$step];
                }
            }
            $scores[$model]['averageavailable'] = $avgscores;
        }
        if (in_array('averageselected',$selected_tasks) or
            in_array($model.':averageselected',$selected_tasks) or
            array_key_exists($model.':averageselected',$available_tasks)){
            $avgscores = array();
            $counts = array();
            foreach ($selected_tasks as $selected_task){
                $taskparts = explode(':',$selected_task);
                $task = array_pop($taskparts);
                echo("$selected_task");
                if (substr($task,0,7) == 'average') continue;
                foreach ($tasks[$task] as $step => $score){
                    if (! array_key_exists($step,$avgscores)){
                        $avgscores[$step] = $score;
                        $counts[$step] = 1;
                    }
                    else{
                        $avgscores[$step] += $score;
                        $counts[$step]++;
                    }
                }
            }
            foreach ($avgscores as $step => $score){
                if ($counts[$step]){
                    $avgscores[$step] /= $counts[$step];
                }
            }
            $scores[$model]['averageselected'] = $avgscores;
        }
    }
}

function read_train_stats(&$traintoks, $model, $file, $dir='models'){
    $traintoks[$model] = array();
    $traintoks[$model]['average-score'] = array();
    $lines = file(implode('/',[$dir,$model,'stats',$file]));
    $tokcount = 0;
    $taskcount = 0;
    foreach ($lines as $line) {
        if ($line){
            $line = rtrim($line);
            $parts = explode("\t",$line);
            $taskparts = explode(': ',$parts[0]);
            if (count($taskparts) == 2){
                $task = $taskparts[0];
                $step = $taskparts[1];
                list($toks,$rest) = explode(' ',trim($parts[5]));
                list($srctoks,$trgtoks) = explode('/',$toks);
                if (! array_key_exists($task,$traintoks[$model])){
                    // echo("$model ... $task");
                    $tokcount = 0;
                    $taskcount++;
                }
                $tokcount += $srctoks + $trgtoks;
                $traintoks[$model][$task][$step] = $tokcount;
                if (array_key_exists($step,$traintoks[$model]['average-score']))
                    $traintoks[$model]['average-score'][$step] += $tokcount;
                else
                    $traintoks[$model]['average-score'][$step] = $tokcount;
            }
        }
    }
    if ($taskcount){ 
        foreach ($traintoks[$model]['average-score'] as $step => $count){
            $traintoks[$model]['average-score'][$step] = $count/$taskcount;
        }
    }
}


/*
read scores from csv files in GitHub repo
*/

function read_valid_scores(&$scores, &$tasks, &$srclangs, &$trglangs, &$langpairs, &$types, $model, $file, $dir='models'){
    $lines = file(implode('/',[$dir,$model,'stats',$file]));

    $gpus = array();
    $checkpoints = array();

    $header = array_shift($lines);
    if (strpos($header,'make') === 0) $header = array_shift($lines);
    $header = rtrim($header);
    $parts = explode("\t",$header);
    array_shift($parts);
    array_shift($parts);
    foreach ($parts as $checkpoint){
        $checkpoint = trim($checkpoint);
        array_push($checkpoints,$checkpoint);
    }
    
    $key = '';
    $scores[$model] = array();
    foreach ($lines as $line) {
        if ($line){
            if (strpos($line,'make') === 0) continue;
            $line = rtrim($line);
            $parts = explode("\t",$line);
            $gpu=array_shift($parts);
            $task=array_shift($parts);
            
            array_push($gpus,$gpu);
            // array_push($tasks,$task);
            $tasks[$task] = 1;
            
            $scores[$model][$task] = array();

            if (substr($task,0,7) != 'average'){
                list($type,$srclang,$trglang) = split_task_name($task);
                if ($type) $types[$type] = 1;
                if ($srclang && $trglang){
                    $srclangs[$srclang] = 1;
                    $trglangs[$trglang] = 1;
                    $langpair = implode('-',array($srclang,$trglang));
                    $langpairs[$langpair] = 1;
                }
            }
            
            foreach ($checkpoints as $checkpoint){
                $score = array_shift($parts);
                $scores[$model][$task][$checkpoint] = $score;
            }
        }
    }
    ksort($scores);
}

function score_per_tokenbudget(&$scores,&$traintoks){
    // var_dump($traintoks);
    $ScoresPerTok = array();
    foreach ($scores as $model => $tasks){
        foreach ($tasks as $task => $checkpoints){
            foreach ($checkpoints as $checkpoint => $score){
                $nrtoks = $traintoks[$model][$task][$checkpoint];
                $ScoresPerTok[$model][$task][$nrtoks] = $scores[$model][$task][$checkpoint];
            }
        }
    }
    return $ScoresPerTok;
}

/*
split task names into components
- assumes that we have a format like type_srclang-trglang
- skip splitting entries that start with 'average' (those are not actual tasks but average scores)
*/

function split_task_name($task){
    $srclang = null;
    $trglang = null;
    $type = null;
    if (substr($task,0,7) != 'average'){
        $langs = explode('-',$task);
        $lang1parts = explode('_',$langs[0]);
        if (count($langs) == 2){
            $srclang = count($lang1parts)>1 ? $lang1parts[1] : $langs[0];
            $trglang = $langs[1];
            $srclangs[$srclang] = 1;
            $trglangs[$trglang] = 1;
            $langpair = implode('-',array($srclang,$trglang));
            $langpairs[$langpair] = 1;
        }
        $type = $lang1parts[0];
    }
    return array($type,$srclang,$trglang);
}


/*
filter tasks according to various criteria and display selection checkboxes
- filter by source language (select all tasks of either of the selected source languages)
- filter by target language (select all tasks of either of the selected target languages)
- filter by task type (select all tasks of either of the selected task types)
*/

function filter_tasks(&$available_tasks,
                      &$available_srclangs,
                      &$available_trglangs,
                      &$available_langpairs,
                      &$available_tasktypes,
                      &$selected_tasks,
                      &$selected_srclangs,
                      &$selected_trglangs,
                      &$selected_langpairs,
                      &$selected_tasktypes){

    echo "<tr><td>source languages: </td><td>";
    ksort($available_srclangs);
    foreach ($available_srclangs as $lang => $nr){
        if (in_array($lang,$selected_srclangs)){
            echo("<input checked='1' type='checkbox' name='srclangs[]' value='$lang'>&nbsp;$lang ");
        }
        else{
            echo("<input type='checkbox' name='srclangs[]' value='$lang'>&nbsp;$lang ");
        }
    }
    echo "</td></tr><tr><td>target languages: </td><td>";
    ksort($available_trglangs);
    foreach ($available_trglangs as $lang => $nr){
        if (in_array($lang,$selected_trglangs)){
            echo("<input checked='1' type='checkbox' name='trglangs[]' value='$lang'>&nbsp;$lang ");
        }
        else{
            echo("<input type='checkbox' name='trglangs[]' value='$lang'>&nbsp;$lang ");
        }
    }
    echo "</td></tr><tr><td>task types: </td><td>";
    foreach ($available_tasktypes as $tasktype => $nr){
        if (in_array($tasktype,$selected_tasktypes)){
            echo("<input checked='1' type='checkbox' name='tasktypes[]' value='$tasktype'>&nbsp;$tasktype ");
        }
        else{
            echo("<input type='checkbox' name='tasktypes[]' value='$tasktype'>&nbsp;$tasktype ");
        }
    }

    echo('</td></tr>');

    
    $filtered_tasks = array();
    $filtered_langpairs = array();
    
    foreach ($available_tasks as $task => $nr){
        list($type,$srclang,$trglang) = split_task_name($task);

        if ($type && $selected_tasktypes){
            if (! in_array($type, $selected_tasktypes)){
                continue;
            }
        }

        if ($srclang && $selected_srclangs){
            if (! in_array($srclang, $selected_srclangs)){
                continue;
            }
        }
        if ($trglang && $selected_trglangs){
            if (! in_array($trglang, $selected_trglangs)){
                continue;
            }
        }
        if ($srclang && $trglang){
            $langpair = implode('-',array($srclang,$trglang));
            $filtered_langpairs[$langpair] = 1;
        }
        $filtered_tasks[$task] = 1;
    }


    $available_tasks = $filtered_tasks;
    $available_langpairs = $filtered_langpairs;
    $selected_langpairs = array_intersect($selected_langpairs,array_keys($available_langpairs));

    $tasks = array();
    foreach ($selected_tasks as $task){
        list($model,$taskname) = explode(':',$task);
        if (array_key_exists($taskname,$available_tasks)){
            array_push($tasks,$task);
        }
        elseif (substr($taskname,0,7) == 'average'){
            array_push($tasks,$task);
        }
    }
    return $tasks;
}


/*
model selection form
(not used anymore)
*/


function select_models(&$models, &$selected_models){
    if (count($selected_models) == 0){
        foreach ($models as $m){
            $m = rtrim($m);
            array_push($selected_models,$m);
        }
    }
    foreach ($models as $m){
        $m = rtrim($m);
        list($name,$dir) = explode('/',$m);
        if (in_array($m, $selected_models)){
            echo("<input checked='1' type='checkbox' name='models[]' value='$m'>&nbsp;$name ");
        }
        else {
            echo("<input type='checkbox' name='models[]' value='$m'>&nbsp;$name ");
        }
    }
}



/*
model selection filters:
- display checkboxes for selecting required model name components
- model name components are separated by '-'
- select models that have ALL selected components in their name
*/


function select_model_features(&$models, &$selected_models, &$selected_model_features){
    // echo('<form method="post" style="display: inline;">');
    $features = array();
    foreach ($models as $m){
        $m = rtrim($m);
        list($name,$dir) = explode('/',$m);
        $feats = explode('-',$name);
        foreach ($feats as $feat)
            array_push($features,$feat);
    }
    $features = array_unique($features);

    // var_dump($selected_model_features);
    echo('<tr><td>models:</td><td>');
    foreach ($features as $feature){
        if (in_array($feature, $selected_model_features)){
            echo("<input checked='1' type='checkbox' name='features[]' value='$feature'>&nbsp;$feature ");
        }
        else {
            echo("<input type='checkbox' name='features[]' value='$feature'>&nbsp;$feature ");
        }
    }
    echo('</td></tr>');

    foreach ($models as $m){
        $m = rtrim($m);
        list($name,$dir) = explode('/',$m);
        $feats = explode('-',$name);
        $model_ok = true;
        foreach ($selected_model_features as $f){
            if (! in_array($f,$feats)){
                $model_ok = false;
            }
        }
        if ($model_ok)
            array_push($selected_models,$m);
    }
    $selected_models = array_unique($selected_models);
}


/*
display model tasks that can be selected
display language pairs that can be selected
*/

function model_tasks(&$models, &$available_tasks, &$langpairs, &$scores,
                     &$selected_models,
                     &$selected_tasks,
                     &$selected_types, &$selected_langpairs,
                     $file='valid-scores-bleu.txt'){

    global $xaxis;
    echo('<p><input type="submit" name="submit" value="plot graph" />');
    echo('<button type="button" onclick="resetSelected();">reset</button> ');
    
    echo("<input type=\"hidden\" name=\"file\" value=\"$file\" />");
    echo('<input type="radio" id="valid-scores-bleu" name="file" value="valid-scores-bleu.txt"');
    if ($file == 'valid-scores-bleu.txt') echo(' checked="checked"');
    echo('><label for="valid-scores-bleu">BLEU</label></input> ');
    echo('<input type="radio" id="valid-scores-chrf" name="file" value="valid-scores-chrf.txt"');
    if ($file == 'valid-scores-chrf.txt') echo(' checked="checked"');
    echo('><label for="valid-scores-chrf">ChrF</label></input> ');
    echo('<input type="radio" id="valid-scores-ppl" name="file" value="valid-scores-ppl.txt"');
    if ($file == 'valid-scores-ppl.txt') echo(' checked="checked"');
    echo('><label for="valid-scores-bleu">perplexity</label></input> ');
    echo('<input type="radio" id="xaxis-training-steps" name="xaxis" value="training-steps"');
    if ($xaxis == 'training-steps') echo(' checked="checked"');
    echo('><label for="xaxis-training-steps">score per training-steps</label></input> ');
    echo('<input type="radio" id="xaxis-consumed-tokens" name="xaxis" value="consumed-tokens"');
    if ($xaxis == 'consumed-tokens') echo(' checked="checked"');
    echo('><label for="xaxis-consumed-tokens">score per consumed-tokens</label></input></p>');

    
    echo('<table><tr>');
    echo("<th>languages</th>");
    foreach ($scores as $model => $tasks){
        list($name,$dir) = explode('/',$model);
        echo("<th>$name</th>");
        // $name = str_replace('/','<br/>',$model);
        // echo("<th>$name</th>");
    }
    echo('</tr><tr>');

    echo('<td valign="top">');
    ksort($langpairs);
    foreach ($langpairs as $langpair => $count){
        if (in_array($langpair, $selected_langpairs)){
            echo("<input checked='1' type='checkbox' name='langpairs[]' value='$langpair'> $langpair<br/>");
        }
        else {
            echo("<input type='checkbox' name='langpairs[]' value='$langpair'> $langpair<br/>");
        }
    }
    echo('</td>');
    
    foreach ($scores as $model => $tasks){
        echo('<td valign="top">');
        $tasks['averageavailable'] = null;
        $tasks['averageselected'] = null;
        ksort($tasks);
        foreach ($tasks as $task => $score){
            if (array_key_exists($task, $available_tasks)){
                if (in_array($model.':'.$task, $selected_tasks)){
                    echo("<input checked='1' type='checkbox' name='tasks[]' value='$model:$task'> $task<br/>");
                }
                else {
                    echo("<input type='checkbox' name='tasks[]' value='$model:$task'> $task<br/>");
                }
            }
        }
        echo('</td>');
    }
    echo('</tr></table>');
}



/*
plot scores for each selected model
*/


function scores_plotly(&$scores,&$selected,$xlabel,$ylabel='BLEU'){

    echo('<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>');
    echo('<div id="myPlot" style="width:200%;max-width:960px;max-height:400px"></div><script>');

    echo("\nconst data = [\n");
    $nr = 0;
    foreach ($selected as $sel){
        list($model,$task) = explode(':',$sel);
        list($name,$dir) = explode('/',$model);
        if ($model and $task){
            if (array_key_exists($model,$scores)){
                if (array_key_exists($task,$scores[$model])){
                    $nr++;
                    echo("{ x: [");
                    echo(implode(', ',array_keys($scores[$model][$task])));
                    echo("], y: [");
                    echo(implode(', ',array_values($scores[$model][$task])));
                    echo("], mode: 'lines+markers', name: '$task/$name' },\n");
                }
            }
        }
    }
    echo("];\n");
    if ($ylabel == 'perplexity') $yaxis = "title: '$ylabel', type: 'log'";
    else $yaxis = "title: '$ylabel'";
    echo("const layout = {
showlegend: true,
xaxis:{ title: '$xlabel' },
yaxis:{ $yaxis },
margin: {
    l: 50,
    r: 150,
    b: 100,
    t: 10,
    pad: 4 }
};\n");
    echo('Plotly.newPlot("myPlot", data, layout);');
    echo('</script>');

}



/*
barchart plotting function is not used
*/


function barchart_plotly(&$data){

    /*
    echo('<pre>');
    echo var_dump($data);
    echo('</pre>');
    return;
    */

    echo('<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>');
    echo('<div id="myPlot" style="width:200%;max-width:680px;max-height:400px"></div><script>');

    echo("\n".'const xArray = ["');
    echo(implode('","',array_keys($data)));
    echo('"];');

    echo('const yArray = ["');
    echo(implode('","',array_values($data)));
    echo('"];');

    echo("\n".'const text = ["');
    echo(implode('","',array_keys($data)));
    echo('"];');

    /*
    echo('const colors = ["');
    echo(implode('","',array_values($rgba)));
    echo('"];');
    */
    
    echo("const data = [{");
    echo("x:xArray,");
    echo("y:yArray,");
    echo("text:text,");
    echo('type:"bar",');
    echo('textposition: "auto",');
    // echo('orientation:"v",');
    // echo('marker: {color: colors}');
    echo("}];\n");

    echo("const layout = {
xaxis:{title: '$label'},
margin: {
    l: 50,
    r: 150,
    b: 100,
    t: 10,
    pad: 4 }
};");
    echo('Plotly.newPlot("myPlot", data, layout);');
    //xaxis: { tickangle: -45 },
    //xaxis: { nticks: 50, tickmode: 'auto' },
    echo('</script>');
}



/*
some helper function to handle CGI arguments
*/


function get_param($key, $default){

    // check the query string first and overwrite session variable
    if (isset($_REQUEST[$key])){
        $_SESSION['params'][$key] = test_input($_REQUEST[$key]);
        // echo("return session variable for $key (--".var_dump($_SESSION['params'][$key])."--)</br>");
        return $_SESSION['params'][$key];
    }

    if (! is_array($_SESSION)) $_SESSION=array();
    if (array_key_exists('params', $_SESSION)){
        if (isset($_SESSION['params'][$key])){
            return $_SESSION['params'][$key];
        }
    }
    
    return $default;
}

function set_param($key, $value){
    $_SESSION['params'][$key] = $value;
}

function test_input($data) {
    if (! is_array($data)){
        $data = trim($data);
        $data = stripslashes($data);
        $data = htmlspecialchars($data);
    }
    return $data;
}


function make_query($data){
    if ( isset( $_COOKIE['PHPSESSID'] ) ) {
        return http_build_query($data);
    }
    if (array_key_exists('params', $_SESSION)){
        $params = $_SESSION['params'];
    }
    else{
        $params = array();
    }
    foreach ($data as $key => $value){
        $params[$key] = $value;
    }
    return http_build_query($params);
}



?>
</body>
</html>
