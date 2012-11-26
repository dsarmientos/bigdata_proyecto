$(document).ready(function() {
    bind_word_visualization();
});

function bind_word_visualization() {
	$('#table-btn').click(function(e) {
		e.preventDefault();
		$('#word-cloud').hide();
		$('#word-table').show();
		$(this).toggleClass('active');
		$('#cloud-btn').removeClass('active');
	});
	$('#cloud-btn').click(function(e) {
		e.preventDefault();
		$('#word-table').hide();
		$('#word-cloud').show();
		$(this).toggleClass('active');
		$('#table-btn').removeClass('active');
	});
}