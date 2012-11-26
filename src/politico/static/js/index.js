$(document).ready(function() {
    bind_word_visualization();
	$('#popular-pag li').click(function(e) {
		e.preventDefault();
		var pag = $(this).attr('id');
		if (pag == 'pag-2')
			$.each($('#cps li'), function() {
				var id = $(this).attr('id');
				console.log(id);
				if (id == "cp-3" || id == "cp-4" || id == "cp-5")
					$(this).show();
				else
					$(this).hide();
			});
		if (pag == 'pag-1')
			$.each($('#cps li'), function() {
				var id = $(this).attr('id');
				console.log(id);
				if (id == "cp-0" || id == "cp-1" || id == "cp-2")
					$(this).show();
				else
					$(this).hide();
			});
		if (pag == 'pag-3')
			$.each($('#cps li'), function() {
				var id = $(this).attr('id');
				console.log(id);
				if (id == "cp-6" || id == "cp-7" || id == "cp-8")
					$(this).show();
				else
					$(this).hide();
			});
	$.each($('.pagination li'), function() {
		    $(this).removeClass('active');
		});
	    $(this).addClass('active');
	});
		
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