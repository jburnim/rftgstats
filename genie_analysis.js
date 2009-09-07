var img_ids = [
	       "production", 
	       "dev", 
	       "military",
	       "bluebrown", 
	       "5vp", 
	       "6dev", 
	       "6powers", 
	       "discard", 
	       "4types", 
	       "alien"
	       ];
var imgs = [];

var homeworld_colors = {'Alpha Centauri': '#663300',
			'Epsilon Eridani': '#0099FF',
			'Old Earth': '#000099',
			'Ancient Race': '#66FF00',
			'Damaged Alien Factory': '#FFFF00',
			"Earth's Lost Colony": '#00CCFF',
			'New Sparta': '#FF0000',
			'Separatist Colony': '#555555',
			'Doomed world': '#000000'};
 
function LoadImages() {
    for (var i = 0; i < img_ids.length; ++i) {
	var new_img = Image();
	new_img.src = 'images/' + img_ids[i] + '.png';
	imgs.push(new_img);
    }
}


function RenderHomeworldGoalData(canvas_id, data) {
    LoadImages();
    window.onload = function() {
	var canvas = document.getElementById(canvas_id);
	var context = canvas.getContext('2d');
	var fillText = function(a, b, c) { };
	if (context.fillText) {
	    context.font = "12 px sans-serif";
	    fillText = function(a, b, c) { context.fillText(a, b, c) };
	}
	var base_y = 80;
	var mul = 300;

	var w = imgs[0].width;

	context.fillStyle = '#000';
	for (var i = 0; i < imgs.length; ++i) {
	    var top_loc = canvas.height - imgs[i].height;
	    context.drawImage(imgs[i], i * w, top_loc);
	} 


	var MAX_RATE = 1.3;
	var MIN_RATE = .7;
	var LEFTOVERS = canvas.height - imgs[0].height;

	function y_coord(r) {
	    var ret = parseInt((MAX_RATE - r) / (MAX_RATE - MIN_RATE) * LEFTOVERS);
	    if (ret < 0) return 0;
	    if (ret > canvas.height) return canvas.height;
	    return ret;
	}

	context.fillStyle = 'black';
	for (var i = MIN_RATE; i <= MAX_RATE; i += .1) {
	    fillText(("" + (i + .001)).substring(0, 3), 
		     canvas.width - 250, y_coord(i));
	}
	
	for (var i = 0; i < data.length; ++i) {
	    var hw = data[i].homeworld;
	    var hw_col = homeworld_colors[hw];
	    context.fillStyle = hw_col;
	    fillText(hw, canvas.width - 200, (i + 1) * 20 + 150);

	    var space_per_line = (imgs[0].width / imgs.length);
	    var cur_x = parseInt(i * space_per_line * .8 + space_per_line * .1);
	    for (var j = 0; j < data[i].adjusted_rate.length; ++j) {
		var rate = data[i].adjusted_rate[j];
		var pos = y_coord(rate);
		var base = y_coord(data[i].win_rate);
		var height = base - pos;
		
		if (height > 0) {
		    context.fillRect(cur_x, pos, 2, height);
		} else {
		    context.fillRect(cur_x, pos + height, 2, -height);
		}
		context.fillRect(cur_x - 2, base, 5, 5);
		cur_x += w;
	    }
	}
    }
}

/*
window.onload = function() {
    hide_images();
    var elem = document.getElementById('myCanvas');

    if (elem && elem.getContext) {
	var context = elem.getContext('2d');

	if (context) {
	    RenderHomeworldData(context, data);
	}
    }
}
*/