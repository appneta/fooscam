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
                $('#teams, .tag').fadeTo(fade_time, 0);
            } else {
                $('.off-red').text(data['team'][1]['red']['offense']);
                $('.def-red').text(data['team'][1]['red']['defense']);
                $('.off-blue').text(data['team'][0]['blue']['offense']);
                $('.def-blue').text(data['team'][0]['blue']['defense']);
                $('#teams, .tag').fadeTo(fade_time, 1);
            }
        }
    });
}
function getstatus() {
    $.getJSON('/status', function(data) {
        if (data) {
            if (data['status'] == 'blue') {
                settext('.status', 'Blue Wins!');
                pulse('blue');
            } else if (data['status'] == 'red') {
                settext('.status', 'Red Wins!');
                pulse('red');
            } else if (data['status'] == 'tie') {
                settext('.status', 'Tie Game!');
                pulse('yellow');
            } else if (data['status'] == 'gameon') {
                $('#game-info').fadeTo(fade_time, 1);
                settext('.status', 'Game On!');
                getplayers();
                getscores();
            } else if (data['status'] == 'gameoff') {
                // table-open message
                $('#game-info').fadeTo(fade_time, 0);
                $('#teams, .tag').fadeTo(fade_time, 0);
                settext('.status', 'Table Open!');
            }
        }
    });
}

function settext(element, text) {
    if (text != $(element).text()) {
        $(element).fadeTo(fade_time, 0, function() {$(element).text(text);});
        $(element).fadeTo(fade_time, 1);
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
