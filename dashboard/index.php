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


$MarmotGitRaw = 'https://raw.githubusercontent.com/Helsinki-NLP/MARMoT/refs/heads/sandbox';
$model_dir = $MarmotGitRaw.'/models';
$available_models = file($MarmotGitRaw.'/models/models.txt');

$models    = get_param('models', array());
$file      = get_param('file', 'valid-scores-bleu.txt');
$tasks     = get_param('tasks', array());
$types     = get_param('types', array());
$langpairs = get_param('langpairs', array());

$metric = $file == 'valid-scores-bleu.txt' ? 'BLEU' : 'perplexity';


echo('<form method="post">');
echo('<small>');
select_models($available_models, $models);
echo('</small><br/><hr/>');

echo("<h1>MAMMOTH Training Dashboard</h1>");

$scores = array();
$available_langpairs = array();
foreach ($models as $m){
    read_valid_scores($scores, $available_langpairs, rtrim($m), $file, $model_dir);
}
$selected = select_tasks($scores, $tasks, $types, $langpairs);
scores_plotly($scores, $selected, 'training steps', $metric);
model_tasks($available_models, $available_langpairs, $scores, $models, $tasks, $types, $langpairs, $file);
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
                $parts = explode('_',$task);
                $type = array_shift($parts);
                $langpair = implode('-',$parts);
                if (in_array($type, $selected_types)){
                    array_push($selected,$model.':'.$task);
                }
                elseif (in_array($langpair, $selected_langpairs)){
                    array_push($selected,$model.':'.$task);
                }
            }
        }
    }
    if (count($selected) == 0){
        foreach (array_keys($models) as $model){
            array_push($selected,$model.":average-score");
            array_push($selected_tasks,$model.":average-score");
        }
    }
    return $selected;
}


function read_valid_scores(&$scores, &$langpairs, $model, $file, $dir='models'){
    $lines = file(implode('/',[$dir,$model,'stats',$file]));

    $gpus = array();
    $tasks = array();
    $checkpoints = array();

    $header = array_shift($lines);
    if (strpos($header,'make') === 0) $header = array_shift($lines);
    $header = rtrim($header);
    $parts = explode("\t",$header);
    array_shift($parts);
    array_shift($parts);
    foreach ($parts as $checkpoint){
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
            array_push($tasks,$task);
            $scores[$model][$task] = array();
            $taskparts = explode('_',$task);
            array_shift($taskparts);
            if ($taskparts){
                $langpair = implode('-',$taskparts);
                $langpairs[$langpair] = 1;
            }

            foreach ($checkpoints as $checkpoint){
                $score = array_shift($parts);
                $scores[$model][$task][$checkpoint] = $score;
            }
        }
    }
    ksort($scores);
}


function select_models(&$models, &$selected_models){
    // echo('<form method="post" style="display: inline;">');
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
    // echo('<br/><input type="submit" value="select" />');
    // echo('</form>');
}


function model_tasks(&$models, &$langpairs, &$scores,
                     &$selected_models,
                     &$selected_tasks,
                     &$selected_types, &$selected_langpairs,
                     $file='valid-scores-bleu.txt'){

    echo('<p><input type="submit" name="submit" value="plot graph" />');
    echo('<button type="button" onclick="resetSelected();">reset</button> ');
    
    echo("<input type=\"hidden\" name=\"file\" value=\"$file\" />");
    echo('<input type="radio" id="valid-scores-bleu" name="file" value="valid-scores-bleu.txt"');
    if ($file == 'valid-scores-bleu.txt') echo(' checked="checked"');
    echo('><label for="valid-scores-bleu">BLEU</label></input> ');
    echo('<input type="radio" id="valid-scores-ppl" name="file" value="valid-scores-ppl.txt"');
    if ($file == 'valid-scores-ppl.txt') echo(' checked="checked"');
    echo('><label for="valid-scores-bleu">perplexity</label></input></p>');
    
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
        ksort($tasks);
        foreach ($tasks as $task => $score){
            if (in_array($model.':'.$task, $selected_tasks)){
                echo("<input checked='1' type='checkbox' name='tasks[]' value='$model:$task'> $task<br/>");
            }
            else {
                echo("<input type='checkbox' name='tasks[]' value='$model:$task'> $task<br/>");
            }
        }
        echo('</td>');
    }
    echo('</tr></table>');
}


function scores_plotly(&$scores,&$selected,$xlabel,$ylabel='BLEU'){

    echo('<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>');
    echo('<div id="myPlot" style="width:200%;max-width:960px;max-height:400px"></div><script>');

    echo("\nconst data = [\n");
    $nr = 0;
    foreach ($selected as $sel){
        list($model,$task) = explode(':',$sel);
        list($name,$dir) = explode('/',$model);
        if ($model and $task){
            $nr++;
            echo("{ x: [");
            echo(implode(', ',array_keys($scores[$model][$task])));
            echo("], y: [");
            echo(implode(', ',array_values($scores[$model][$task])));
            echo("], mode: 'lines+markers', name: '$task/$name' },\n");
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
