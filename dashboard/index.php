<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">

<html>
<head>
  <title>MAMMOTH Training Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
<?php

session_start();


// $model_dir = 'models';
// $models = get_models($model_dir);

$MarmotGitRaw = 'https://raw.githubusercontent.com/Helsinki-NLP/MARMoT/refs/heads/sandbox';
$model_dir = $MarmotGitRaw;
$models = array('sandbox/tiedeman/oellm-lg/mammoth-flanonly-shuffled',
                'sandbox/tiedeman/oellm-lg/mammoth-docmt4',
                'sandbox/tiedeman/oellm-lg/mammoth-flan-mt-sharedenc',
                'sandbox/tiedeman/oellm-lg/mammoth-flan-mt',
                'models/docmt-langgroup-encoder/mammoth-docmt');

$model = get_param('model', $models[0]);
$file = get_param('file', 'valid-scores-bleu.txt');
$tasks = get_param('tasks', array());
$types = get_param('types', array());
$langpairs = get_param('langpairs', array());
// $tasks = isset($_REQUEST['tasks']) ? $_REQUEST['tasks'] : array();
// $types = isset($_REQUEST['types']) ? $_REQUEST['types'] : array();
// $langpairs = isset($_REQUEST['langpairs']) ? $_REQUEST['langpairs'] : array();



echo('<small>');
foreach ($models as $m){
    echo("[<a href='?model=$m&file=$file'>$m</a>] ");
}
echo('</small><br/><hr/>');

echo("<h1>MAMMOTH Training Dashboard</h1>");

echo("<ul>");
echo("<li><a href='?model=$model&file=valid-scores-bleu.txt'>Validation Scores (BLEU)</a></li>");
echo("<li><a href='?model=$model&file=valid-scores-ppl.txt'>Validation Scores (perplexity)</a></li>");
echo("</ul>");



$scores = read_valid_scores($model, $file, $model_dir);
$selected = select_tasks($scores, $tasks, $types, $langpairs);
scores_plotly($scores,$selected,$file);
model_tasks($scores, $tasks, $types, $langpairs, $file);

    


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
    
    foreach ($scores as $task => $score){
        if (! in_array($task, $selected_tasks)){
            list($type,$langpair) = explode('_',$task);
            if (in_array($type, $selected_types)){
                array_push($selected,$task);
            }
            elseif (in_array($langpair, $selected_langpairs)){
                array_push($selected,$task);
            }
        }
    }
    if (count($selected) == 0)
        array_push($selected,'average-score');
    return $selected;
}


function read_valid_scores($model,$file,$dir='models'){
    $lines = file(implode('/',[$dir,$model,'stats',$file]));

    $gpus = array();
    $tasks = array();
    $checkpoints = array();
    $scores = array();

    $header = array_shift($lines);
    $header = rtrim($header);
    $parts = explode("\t",$header);
    array_shift($parts);
    array_shift($parts);
    foreach ($parts as $checkpoint){
        array_push($checkpoints,$checkpoint);
    }
    
    $key = '';
    foreach ($lines as $line) {
        if ($line){
            $line = rtrim($line);
            $parts = explode("\t",$line);
            $gpu=array_shift($parts);
            $task=array_shift($parts);
            
            array_push($gpus,$gpu);
            array_push($tasks,$task);
            $scores[$task] = array();
            foreach ($checkpoints as $checkpoint){
                $score = array_shift($parts);
                $scores[$task][$checkpoint] = $score;
                // array_push($scores[$task],$score);
            }
        }
    }
    ksort($scores);
    return $scores;
}

function model_tasks(&$scores, &$selected_tasks, &$selected_types, &$selected_langpairs, $file='valid-scores-bleu.txt'){
    echo('<form method="post">');
    echo('<input type="submit" value="plot graph" />');
    echo("<input type=\"hidden\" name=\"file\" value=\"$file\" />");
    echo('<input type="hidden" name="tasks[]" value="dummy" />');
    echo('<table><tr><td valign="top">');
    $types = array();
    $langpairs = array();
    foreach ($scores as $task => $score){
        list($type,$langpair) = explode('_',$task);
        if ($type and $type != 'average-score') $types[$type]++;
        if ($langpair) $langpairs[$langpair]++;
        if (in_array($task, $selected_tasks)){
            echo("<input checked='1' type='checkbox' name='tasks[]' value='$task'> $task<br/>");
        }
        else {
            echo("<input type='checkbox' name='tasks[]' value='$task'> $task<br/>");
        }
    }
    echo('</td>');
    if (count($langpairs) > 1 and count($langpairs) < count($scores) - 1 ){
        echo('<td valign="top">');
        echo('<input type="hidden" name="langpairs[]" value="dummy" />');
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
    }
    if (count($types) > 1 and count($types) < count($scores) - 1){
        ksort($types);
        echo('<td valign="top">');
        echo('<input type="hidden" name="types[]" value="dummy" />');
        foreach ($types as $type => $count){
            if (in_array($type, $selected_types)){
                echo("<input checked='1' type='checkbox' name='types[]' value='$type'> $type<br/>");
            }
            else {
                echo("<input type='checkbox' name='types[]' value='$type'> $type<br/>");
            }
        }
        echo('</td>');
    }
    echo('</tr></table></form>');
}


function scores_plotly(&$scores,&$selected,$label){
    
    echo('<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>');
    echo('<div id="myPlot" style="width:200%;max-width:680px;max-height:400px"></div><script>');

    echo("\nconst data = [\n");
    foreach ($selected as $sel){
        echo("{ x: [");
        echo(implode(', ',array_keys($scores[$sel])));
        echo("], y: [");
        echo(implode(', ',array_values($scores[$sel])));
        echo("], mode: 'lines+markers', name: '$sel' },\n");
    }
    echo("];\n");    
    echo("const layout = {
xaxis:{title: '$label'},
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
