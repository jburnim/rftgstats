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
 
function LoadImages() {
    for (var i = 0; i < img_ids.length; ++i) {
	var new_img = Image();
	new_img.src = 'images/' + img_ids[i] + '.png';
	imgs.push(new_img);
    }
}

function RenderHomeworldGoalData(canvas_id, data) {
    LoadImages();
    data = data[0]; // fix HACK
    window.onload = function() {
	var context = document.getElementById(canvas_id).getContext('2d');
	
	var base_y = 80;
	var mul = 300;
	context.font = "12 px sans-serif";
	context.fillText(data.homeworld, 0, 140);
	var base_line = data.win_rate;
	context.fillStyle = '#f00';
	var w = imgs[0].width;
	context.fillRect(0, base_y, 10 * w, 3);

	context.fillStyle = '#000';
	var cur_x = 0;

	for (var i = 0; i < imgs.length; ++i) {
	    context.drawImage(imgs[i], cur_x, 100);
	    var rate = data.adjusted_rate[i];
	    var y = base_y + (1 - rate) * mul;
	    context.fillRect(cur_x + w/2, y, 10, 10);
	    cur_x += w;
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