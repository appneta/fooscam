$(document).ready(function() {
    var history_url = $('#hist-url').attr('href');
    $('#foos-stats').dataTable( {
        'bProcessing': true,
        'aaSorting' : [[7, 'desc']],
        'sAjaxSource': history_url
    } );
});
