/*
    MAMMOTH training dashboard - the behaviour of the page in the browser.

    php hands the per-request data over inline in the html (BAR_FILE,
    BAR_TASKS, BAR_DATA and the draws that follow them); everything the
    page does with that data lives here.
*/

function resetSelected() {
  var inputs=document.getElementsByTagName("input");
  for (var i in inputs)
      if (inputs[i].type=="checkbox"){
          // the filters drop every narrowing, the model selection does not:
          // resetting means "show all models that pass the filters"
          inputs[i].checked = (inputs[i].name == "selmodels[]");
      }
}

// check or uncheck every model of the model selection block at once
function setModelSelection(all) {
  var inputs=document.getElementsByName("selmodels[]");
  for (var i = 0; i < inputs.length; i++) inputs[i].checked = all;
}

/*
    Cut a bar chart payload down to the tasks the filters left.

    php hands that list over in BAR_TASKS, and it is the same list the task
    checkboxes below the plots are rendered from. The scores of a model
    always arrive with every task of that model, so the parallel arrays of
    the payload (tasks, colours, scores per checkpoint, final scores) are
    rebuilt over the indices that are still allowed. The payload of the
    "all selected models" choice is cut the same way, except that its score
    and final score rows hold one entry per model and the task index is cut
    out of every one of them. The payload is returned unchanged when nothing
    is filtered out.
*/

function filterBarTasks(data){
  if (!BAR_TASKS || !data || !data.tasks) return data;
  var keep = [];
  for (var i = 0; i < data.tasks.length; i++)
      if (BAR_TASKS.indexOf(data.tasks[i]) != -1) keep.push(i);
  if (keep.length == data.tasks.length) return data;   // nothing to drop

  var filtered = {};
  for (var key in data) filtered[key] = data[key];
  filtered.tasks = []; filtered.scores = {};
  for (var j = 0; j < keep.length; j++)
    filtered.tasks.push(data.tasks[keep[j]]);

  if (data.all){
    // one row per model, so the task index is cut out of every model's row
    filtered.last = []; filtered.lastAt = [];
    for (var m = 0; m < data.last.length; m++){
      var lasts = [], ats = [];
      for (var k = 0; k < keep.length; k++){
        lasts.push(data.last[m][keep[k]]);
        ats.push(data.lastAt[m][keep[k]]);
      }
      filtered.last.push(lasts); filtered.lastAt.push(ats);
    }
    for (var ckpt in data.scores){
      var rows = data.scores[ckpt], picked = [];
      for (var n = 0; n < rows.length; n++){
        var row = [];
        for (var p = 0; p < keep.length; p++) row.push(rows[n][keep[p]]);
        picked.push(row);
      }
      filtered.scores[ckpt] = picked;
    }
  } else {
    filtered.colors = [];
    filtered.last = []; filtered.lastAt = [];
    for (var t = 0; t < keep.length; t++){
      filtered.colors.push(data.colors[keep[t]]);
      filtered.last.push(data.last[keep[t]]);
      filtered.lastAt.push(data.lastAt[keep[t]]);
    }
    for (var name in data.scores){
      var one = data.scores[name], picked2 = [];
      for (var q = 0; q < keep.length; q++) picked2.push(one[keep[q]]);
      filtered.scores[name] = picked2;
    }
  }
  return filtered;
}

/*
    Bar chart of the validation score of every task of one model, or of every
    selected model at once when the drop-down says so.

    The scores of all checkpoints are handed over by php in BAR_DATA, so the
    chart can be moved to another checkpoint in the browser: pickBarChart()
    chooses the scores, orders the tasks best first and builds the series,
    and drawBarChart() hands those to plotly. A task that does not reach the
    requested checkpoint falls back to its own last one. With every model
    there is one series of bars per model and the tasks stay in task order.
*/

// the scores of the model in the bar chart, handed over by php; null while no
// model is selected
var BAR_DATA = null;
// the score file this page was rendered with, so that a swapped-in model is
// read for the same metric
var BAR_FILE = '';
// the tasks the filters left, handed over by php: the bar chart shows these
// tasks and no others, for the model of the page as well as for a model
// chosen in the drop-down later
var BAR_TASKS = null;
// whether the bars are the diff against the previous checkpoint rather than
// the score itself; php hands the option over with the page
var BAR_DIFF = false;
// the drop-down value that means "every selected model", the same as
// BARCHART_ALL in php; that choice reloads the page rather than fetching
var BAR_CHART_ALL = '(all)';
var barChartDrawn = false;
var barChartRequest = null;   // the model whose scores are being fetched

/*
    The diff of a checkpoint is measured against the one before it, and that
    is what this finds: "last" stands for the final checkpoint, and the first
    checkpoint has no predecessor at all.
*/

function previousCheckpoint(ckpt) {
  var list = BAR_DATA.checkpoints;
  var idx = (ckpt === "last") ? list.length - 1 : list.indexOf(String(ckpt));
  return idx > 0 ? list[idx - 1] : null;
}

// the status line that describes the chart as a whole
function barChartSummary() {
  var models = BAR_DATA.models ? BAR_DATA.models.length + " models, " : "";
  return BAR_DATA.model + ": " + models + BAR_DATA.tasks.length + " tasks, "
         + BAR_DATA.checkpoints.length + " checkpoints";
}

function pickBarChart(ckpt) {
  var row = (ckpt === "last") ? null : BAR_DATA.scores[ckpt];
  if (!row && ckpt !== "last") {          // unknown checkpoint: take the final one
    ckpt = BAR_DATA.checkpoints[BAR_DATA.checkpoints.length - 1];
    row = BAR_DATA.scores[ckpt];
  }
  // with the diff option every bar is the difference against the checkpoint
  // before the shown one; a side without a score falls back to the task's
  // final score just as it does without the option, which leaves a task that
  // stopped being evaluated at a diff of zero. The first checkpoint has no
  // predecessor, so nothing is subtracted there: its diff is the score
  // itself, the difference against zero
  var previous = BAR_DIFF ? previousCheckpoint(ckpt) : null;
  var prevRow = previous ? BAR_DATA.scores[previous] : null;

  // every selected model: one series of bars per model, in the task order the
  // payload arrives in rather than sorted by score, and a task without a
  // score stays a gap instead of pulling the other models out of line
  if (BAR_DATA.all) {
    var series = [], any = false;
    for (var m = 0; m < BAR_DATA.models.length; m++) {
      var values = [], at = [];
      for (var i = 0; i < BAR_DATA.tasks.length; i++) {
        var haveM = row && row[m] && row[m][i] !== null && row[m][i] !== undefined;
        var lastM = BAR_DATA.last[m][i];
        var value = haveM ? row[m][i] : lastM;
        if (value === null) { values.push(null); at.push(null); continue; }
        if (prevRow && prevRow[m]) {
          var prevM = (prevRow[m][i] !== null && prevRow[m][i] !== undefined)
                    ? prevRow[m][i] : lastM;
          if (prevM !== null) value -= prevM;
        }
        any = true;
        values.push(value);
        at.push(haveM ? ckpt : BAR_DATA.lastAt[m][i]);
      }
      series.push({name: BAR_DATA.models[m], color: BAR_DATA.modelColors[m],
                   scores: values, at: at});
    }
    return {checkpoint: ckpt, previous: previous,
            tasks: any ? BAR_DATA.tasks : [], series: series};
  }

  var bars = [];
  for (var i = 0; i < BAR_DATA.tasks.length; i++) {
    var have = row && row[i] !== null && row[i] !== undefined;
    var score = have ? row[i] : BAR_DATA.last[i];
    if (score === null) continue;          // this task has no score at all
    if (prevRow){
      var prev = (prevRow[i] !== null && prevRow[i] !== undefined)
               ? prevRow[i] : BAR_DATA.last[i];
      if (prev !== null) score -= prev;
    }
    bars.push({task: BAR_DATA.tasks[i], score: score,
               at: have ? ckpt : BAR_DATA.lastAt[i],
               color: BAR_DATA.colors[i]});
  }
  var dir = BAR_DATA.descending ? -1 : 1;
  bars.sort(function (a, b) { return dir * (a.score - b.score); });
  return {
    checkpoint: ckpt,                      // the one really drawn
    previous: previous,                    // diffs are measured against it
    tasks: bars.map(function (b) { return b.task; }),
    scores: bars.map(function (b) { return b.score; }),
    at: bars.map(function (b) { return b.at; }),
    colors: bars.map(function (b) { return b.color; }),
    // the one series a single model makes: bars coloured per task and,
    // without a name, no legend entry
    series: [{name: null, color: bars.map(function (b) { return b.color; }),
              scores: bars.map(function (b) { return b.score; }),
              at: bars.map(function (b) { return b.at; })}]
  };
}

function barChartLayout(ckpt, previous) {
  var shown = (ckpt === "last") ? "last checkpoint" : "checkpoint " + ckpt;
  // diffs are differences rather than scores: they can be negative, so the
  // log axis perplexity would want would swallow half of them
  var layout;
  if (BAR_DIFF){
    layout = {
      title: {text: BAR_DATA.model + " - " + BAR_DATA.metric + " diff per task (from "
              + (previous === null ? "zero" : "checkpoint " + previous)
              + " to " + shown + ")",
              font: {size: 13}},
      xaxis: {title: "", tickangle: -45, automargin: true},
      yaxis: {title: "diff in " + BAR_DATA.metric},
      margin: {l: 60, r: 30, b: 120, t: 40, pad: 4}
    };
  } else {
    layout = {
      title: {text: BAR_DATA.model + " - " + BAR_DATA.metric + " per task (" + shown + ")",
              font: {size: 13}},
      xaxis: {title: "", tickangle: -45, automargin: true},
      yaxis: BAR_DATA.log ? {title: BAR_DATA.metric, type: "log"}
                          : {title: BAR_DATA.metric},
      margin: {l: 60, r: 30, b: 120, t: 40, pad: 4}
    };
  }
  // with every model there is one group of bars per task, and the model
  // names take the room to the right of the plot as a legend
  if (BAR_DATA.all){
    layout.barmode = "group";
    layout.showlegend = true;
    layout.legend = {x: 1, xanchor: "left"};
    layout.margin = {l: 60, r: 190, b: 120, t: 40, pad: 4};
  }
  return layout;
}

function drawBarChart(ckpt) {
  // every score but perplexity takes the first checkpoint as a diff against
  // zero; a perplexity without a checkpoint before it is refused
  if (BAR_DIFF && BAR_DATA.metric === 'perplexity' && !previousCheckpoint(ckpt)){
    var shown = (ckpt === "last") ? "the last checkpoint" : "checkpoint " + ckpt;
    barChartStatus('no diff to show: ' + shown + ' has no checkpoint before it');
    return;
  }
  var bars = pickBarChart(ckpt);
  if (!bars.tasks.length) return;
  // one trace per model: a single model keeps one colour per task and goes
  // into the chart nameless, every model of the choice gets its own name and
  // colour and shows up in the legend
  var traces = [];
  for (var s = 0; s < bars.series.length; s++){
    var series = bars.series[s];
    var named = series.name !== null && series.name !== undefined;
    var trace = {type: "bar", x: bars.tasks, y: series.scores,
                 customdata: series.at, marker: {color: series.color},
                 hovertemplate: (named ? "%{fullData.name}<br>" : "")
                   + "%{x}<br>" + BAR_DATA.metric
                   + (BAR_DIFF
                      ? " diff " + (bars.previous === null ? "from zero"
                                                           : "since checkpoint " + bars.previous)
                        + ": %{y:.2f}<extra></extra>"
                      : ": %{y:.2f}<br>checkpoint %{customdata}<extra></extra>")};
    if (named) trace.name = series.name;
    traces.push(trace);
  }
  var layout = barChartLayout(bars.checkpoint, bars.previous);
  // the first draw creates the plot, later ones only redraw it
  if (barChartDrawn) Plotly.react("barPlot", traces, layout);
  else { barChartDrawn = true; Plotly.newPlot("barPlot", traces, layout); }
  // a draw in diff mode may have replaced the complaint about a missing
  // predecessor, so the line describing the chart as a whole goes back on
  if (BAR_DIFF) barChartStatus(barChartSummary());
}

/*
    Switching the model in the drop-down fetches that model's scores and
    redraws, so that the chart does not have to wait for a page reload. The
    request goes to the same script, which answers with json and stops. The
    choice "all selected models" is the exception: its scores are not read
    for one model, so it submits the form and the page comes back with them.
*/

// the model as it is named in the drop-down, without the training data suffix
function barChartModelName(model) {
  return String(model).replace(/\/[^/]*$/, '');
}

function barChartStatus(text, isError) {
  var status = document.getElementById('barStatus');
  if (!status) return;
  status.textContent = text;
  status.className = isError ? 'hint error' : 'hint';
}

// the heading and the slider are only there while there is a chart to go with
// them; php renders them hidden when the page opens without one
function showBarChartSection(show) {
  var head = document.getElementById('barhead');
  if (head) head.hidden = !show;
}

// scroll the chart into view, but only when it is not on screen already
function revealBarChart(plot) {
  if (!plot || !plot.getBoundingClientRect) return;
  var box = plot.getBoundingClientRect();
  if (box.top < 0 || box.bottom > window.innerHeight) plot.scrollIntoView();
}

function loadBarChartModel(model) {
  var slider = document.getElementById('barchartckpt');
  var readout = document.getElementById('barchartckptval');
  var plot = document.getElementById('barPlot');

  // a request that is still running is no longer wanted; the field is cleared
  // first, so that the handler of the abandoned request does not report it
  if (barChartRequest){
    var stale = barChartRequest;
    barChartRequest = null;
    stale.abort();
  }

  if (!model){                   // "(none)": there is nothing left to show
    BAR_DATA = null;
    barChartDrawn = false;
    if (plot){ Plotly.purge(plot.id); plot.className = 'empty'; }
    showBarChartSection(false);
    if (slider){
      slider.disabled = true;
      slider.setAttribute('aria-valuetext', 'last');
      if (readout) readout.textContent = 'last';
    }
    barChartStatus('choose a model to see its scores per task');
    return;
  }

  // the scores of every selected model are not part of this page, so the
  // choice is submitted and the page comes back with all of them charted;
  // the checkpoint slider then works from that page's payload
  if (model === BAR_CHART_ALL){
    var picker = document.getElementById('barchart');
    if (picker && picker.form) picker.form.submit();
    return;
  }

  var name = barChartModelName(model);
  barChartStatus('loading the scores of ' + name + ' ...');
  var request = new XMLHttpRequest();
  barChartRequest = request;
  var expdirParam = '';
  try {
    var expdirEl = document.querySelector ? document.querySelector('input[name="expdir"]:checked') : null;
    if (expdirEl && expdirEl.value) expdirParam = '&expdir=' + encodeURIComponent(expdirEl.value);
  } catch (e) {
    expdirParam = '';
  }
  request.open('GET', '?barchartdata=' + encodeURIComponent(model)
                  + '&file=' + encodeURIComponent(BAR_FILE)
                  + expdirParam, true);
  request.onload = function(){
    if (request !== barChartRequest) return;   // a later choice has won
    barChartRequest = null;
    var data = null;
    try { data = JSON.parse(request.responseText); } catch (e) { data = null; }
    if (!data || data.error){
      // keep showing the previous model rather than an empty chart
      barChartStatus('could not load the scores of ' + name, true);
      return;
    }

    // only the tasks the filters left are shown, also for a model that was
    // chosen in the drop-down after the page was rendered
    BAR_DATA = filterBarTasks(data);
    barChartDrawn = false;       // a different model, so draw it from scratch
    if (slider){
      slider.max = String(data.checkpoints.length);
      slider.value = '0';                      // a new model starts at "last"
      slider.setAttribute('aria-valuetext', 'last');
      if (readout) readout.textContent = 'last';
    }
    if (!BAR_DATA.tasks.length){                // every task is filtered out
      if (plot){ Plotly.purge(plot.id); plot.className = 'empty'; }
      showBarChartSection(false);
      if (slider) slider.disabled = true;
      barChartStatus('no task of ' + data.model + ' is left by the filters');
      return;
    }
    if (plot) plot.className = '';
    showBarChartSection(true);
    if (slider) slider.disabled = false;
    barChartStatus(barChartSummary());
    drawBarChart('last');
    revealBarChart(plot);
  };
  request.onerror = request.onabort = function(){
    if (request !== barChartRequest) return;
    barChartRequest = null;
    barChartStatus('could not load the scores of ' + name, true);
  };
  request.send();
}

/*
    The button in the filter block sends the form as it stands to the script,
    which answers with the two selection lists as json - the lists follow the
    filters, while the plots below stay as they are until "plot graph". The
    hints in the block headers come back with the lists.
*/

function updateSelectionLists(){
  var form = document.getElementById('pageform');
  var button = document.getElementById('updatelists');
  var status = document.getElementById('updatestatus');
  if (!form) return;
  if (status) status.textContent = 'updating ...';
  if (button) button.disabled = true;

  var data = new FormData(form);
  data.append('updatelists', '1');

  fetch(window.location.pathname + window.location.search, {method: 'POST', body: data})
    .then(function(response){
      if (!response.ok) throw new Error('status ' + response.status);
      return response.json();
    })
    .then(function(answer){
      var modellist = document.getElementById('modellist');
      if (modellist && typeof answer.modellist == 'string') modellist.innerHTML = answer.modellist;
      var tasklist = document.getElementById('tasklist');
      if (tasklist && typeof answer.tasklist == 'string') tasklist.innerHTML = answer.tasklist;
      var filterhint = document.getElementById('filterhint');
      if (filterhint && typeof answer.filterhint == 'string') filterhint.textContent = answer.filterhint;
      var selhint = document.getElementById('selhint');
      if (selhint && typeof answer.selhint == 'string') selhint.textContent = answer.selhint;
      if (status) status.textContent = 'the lists are updated';
    })
    .catch(function(){
      if (status) status.textContent = 'could not update the lists';
    })
    .then(function(){
      if (button) button.disabled = false;
    });
}

// once the page is there, wire the controls up: which of them redraw the
// chart themselves, and which state has to be handed to the form
window.addEventListener('load', function(){
  // the button in the filter block refreshes the two selection lists after a
  // filter has changed, without a reload and without touching the plots
  var updateButton=document.getElementById('updatelists');
  if (updateButton){
    updateButton.addEventListener('click', updateSelectionLists);
  }

  // the filter block is open or collapsed, and that has to survive a reload
  var box=document.getElementById('modelselect');
  var state=document.getElementById('showmodels');
  if (box && state){
    box.addEventListener('toggle', function(){
      state.value = box.open ? '1' : '0';
    });
  }

  // ...and the same for the block that picks models out of the filtered list
  var selbox=document.getElementById('modelsel');
  var selstate=document.getElementById('showselmodels');
  if (selbox && selstate){
    selbox.addEventListener('toggle', function(){
      selstate.value = selbox.open ? '1' : '0';
    });
  }

  // ...and for the block that picks tasks out of the filtered list
  var taskbox=document.getElementById('taskselect');
  var taskstate=document.getElementById('showtasks');
  if (taskbox && taskstate){
    taskbox.addEventListener('toggle', function(){
      taskstate.value = taskbox.open ? '1' : '0';
    });
  }

  // choosing another model loads its scores, no reload needed
  var barSelect=document.getElementById('barchart');
  if (barSelect){
    barSelect.addEventListener('change', function(){
      loadBarChartModel(barSelect.value);
    });
  }

  // moving the checkpoint slider redraws the bar chart in place, no reload.
  // it is wired up whether or not a model is chosen already, because a model
  // picked in the drop-down turns the same slider into a live control
  var slider=document.getElementById('barchartckpt');
  var readout=document.getElementById('barchartckptval');
  if (slider){
    var queued=false;
    slider.addEventListener('input', function(){
      if (!BAR_DATA) return;             // still no model to show
      // dragging fires one event per step, so draw at most one frame at a time
      if (queued) return;
      queued=true;
      var draw=function(){
        queued=false;
        var position=parseInt(slider.value, 10);
        var ckpt=position>0 ? BAR_DATA.checkpoints[position-1] : 'last';
        if (!ckpt) ckpt='last';
        if (readout) readout.textContent=ckpt;
        // a screen reader would otherwise announce the position, not the step
        slider.setAttribute('aria-valuetext', ckpt);
        drawBarChart(ckpt);
      };
      if (window.requestAnimationFrame) window.requestAnimationFrame(draw); else draw();
    });
  }
});
