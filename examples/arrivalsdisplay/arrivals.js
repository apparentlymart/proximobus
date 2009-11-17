
var stopId = 16995;
if (window.location.hash != "" && window.location.hash != "#") {
    stopId = window.location.hash.substr(1);
}

var stopInfoURL = "http://proximobus.appspot.com/agencies/sf-muni/stops/"+stopId+".js?callback=?";
var stopRoutesURL = "http://proximobus.appspot.com/agencies/sf-muni/stops/"+stopId+"/routes.js?callback=?";
var stopMessagesURL = "http://proximobus.appspot.com/agencies/sf-muni/stops/"+stopId+"/messages.js?callback=?";
var stopPredictionsURL = "http://proximobus.appspot.com/agencies/sf-muni/stops/"+stopId+"/predictions.js?callback=?";

var routeNames = {}
var runNames = {}
var routeCount = 0;
var routesLoadedCount = 0;
var gotRouteNames = false;
var gotStopInfo = false;

function allReady() {
    return gotRouteNames && gotStopInfo && (routeCount == routesLoadedCount);
}

function poll() {
    $.getJSON(stopPredictionsURL, handlePredictions);
}

function startPolling() {
    if (allReady()) {
	poll();
    }
}

function routeRunsURL(routeId) {
    return "http://proximobus.appspot.com/agencies/sf-muni/routes/"+routeId+"/runs.js?callback=?";
}

function handleRouteRunsList(data) {
    runs = data.items;
    for (var i = 0; i < runs.length; i++) {
	run = runs[i];
	runNames[run.id] = run.display_name;
    }
    routesLoadedCount++;
    startPolling();
}

function handleRoutesList(data) {
    routes = data.items;
    routeCount = routes.length;
    for (var i = 0; i < routes.length; i++) {
	route = routes[i];

	routeNames[route.id] = route.display_name;
	$.getJSON(routeRunsURL(route.id), handleRouteRunsList);
    }
    routeIds = routes.map(function (i) { return i.id }).sort();
    $("#routelist").html('');
    for (var i = 0; i < routeIds.length; i++) {
	var elem = $('<li></li>');
	$(elem).text(routeIds[i]);
	$("#routelist").append(elem);
    }

    gotRouteNames = true;
    startPolling();
}


function handleStopInfo(data) {
    $("#stopname").text(data["title"]);
    gotStopInfo = true;
    startPolling();
}

function handleMessagesList(data) {
    $("#messages").html('');
    messages = data.items;

    for (var i = 0; i < messages.length; i++) {
	var elem = $('<li></li>');
	$(elem).text(messages[i]);
	$("#messages").append(elem);
    }

    $("#messagescontainer").jCarouselLite(
	{
	    vertical: true,
	    visible: 1,
	    auto: messages.length > 1 ? 3000 : 0,
	    speed: 1000
	}
    );
}

function handlePredictions(data) {
    setTimeout(poll, 30000);

    $("#predictions").html('');

    predictions = data.items;

    if (predictions.length == 0) {
	$("#predictions").html('<li><div class="none">No Arrivals Predicted</div></li>');
	return;
    }

    for (var i = 0; i < predictions.length; i++) {
	var elem = $('<li><div class="route"></div><div class="time"></div><div class="run"></div></li>');
	prediction = predictions[i];

	$(elem).find('.route').text(routeNames[prediction.route_id]);
	$(elem).find('.run').text(runNames[prediction.run_id]);

	var minutes = prediction.minutes;
	var timeCaption;
	if (minutes == 0) {
	    timeCaption = prediction.is_departing ? "Departing" : "Arriving";
	}
	else {
	    timeCaption = minutes+" min";
	}

	$(elem).find('.time').text(timeCaption);

	$("#predictions").append(elem);
    }

}

$(document).ready(function() {
    $.getJSON(stopInfoURL, handleStopInfo);
    $.getJSON(stopRoutesURL, handleRoutesList);
    $.getJSON(stopMessagesURL, handleMessagesList);
});



