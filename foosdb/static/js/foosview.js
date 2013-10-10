$(document).ready(update_ui());
var fade_time = 250
function getscores() {
  $.getJSON('/score', function(data) {
   if (data) {
       settext('#score-red', String(data['score']['red']));
       settext('#score-blue', String(data['score']['blue']));
    }
  });
}
function getplayers() {
    $.getJSON('/players', function(data) {
        if (data) {
            //holy crap I miss multiple comparison!
            if (data['team'][1]['red']['offense'] == 'None' && 
                data['team'][1]['red']['defense'] == 'None' &&
                data['team'][0]['blue']['offense'] == 'None' &&
                data['team'][0]['blue']['defense'] == 'None') {
                $('#teams, .tag').fadeOut(fade_time);
            } else {
                $('.off-red').text(data['team'][1]['red']['offense']);
                $('.def-red').text(data['team'][1]['red']['defense']);
                $('.off-blue').text(data['team'][0]['blue']['offense']);
                $('.def-blue').text(data['team'][0]['blue']['defense']);
                $('#teams, .tag').fadeIn(fade_time);
            }
        }
    });
}
function getstatus() {
    $.getJSON('/status', function(data) {
        if (data) {
            if (data['status'] == 'blue') {
                pulse('blue');
                settext('.status', 'Blue Wins!');
                $('#score','#teams', '#cam-frame').fadeOut(fade_time);
            } else if (data['status'] == 'red') {
                pulse('red');
                settext('.status', 'Red Wins!');
                $('#score','#teams', '#cam-frame').fadeOut(fade_time);
            } else if (data['status'] == 'tie') {
                pulse('yellow');
                settext('.status', 'Tie Game!');
                $('#score','#teams', '#cam-frame').fadeOut(fade_time);
            } else if (data['status'] == 'Game On!') {
                $('#score','#teams', '#cam-frame').fadeIn(fade_time);
                settext('.status', data['status']);
                getplayers();
                getscores();
            } else {
                // table-open message
                settext('.status', data['status']);
            }
        }
    });
}

function settext(element, text) {
    if (text != $(element).text()) {
        $(element).fadeOut(fade_time, function() {$(element).text(text);});
        $(element).fadeIn(fade_time);
    }
}
function pulse(color) {
    for (var x=0; x < 3; x++) {
        $('.status').animate({'color': color}, 350)
        .animate({'color': 'black'}, 350);
    }
}
function update_ui() {
    $('.foos-title').fadeIn(fade_time);
    /*getscores();
    getplayers();*/
    getstatus();
    setTimeout(update_ui, 2000);
}
