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

function RenderCardWinInfo(data, canvas) {
  var context = canvas.getContext("2d"), height = canvas.height, width = canvas.width,
      location = [], card, x, y;

  // Draw axis.
  context.fillRect(0, 0, 2, height);
  context.fillRect(0, height - 2, width, 2);

  // Compute scales.
  var maxExpWins = Number.MIN_VALUE, minExpWins = Number.MAX_VALUE, maxWinRate = Number.MIN_VALUE,
      minWinRate = Number.MAX_VALUE;

  for (var name in data) {
    card = data[name];
    maxExpWins = Math.max(maxExpWins, card["exp_wins"]);
    minExpWins = Math.min(minExpWins, card["exp_wins"]);
    maxWinRate = Math.max(maxWinRate, card["win_rate"]);
    minWinRate = Math.min(minWinRate, card["win_rate"]);
  }

  // Draw dots.
  for (name in data) {
    card = data[name];
    x = parseInt((0.05 * width) + card["exp_wins"] /
                                  (maxExpWins - minExpWins) * width * 0.9);
    y = parseInt((0.05 * height) + (maxWinRate - card["win_rate"]) /
                                   (maxWinRate - minWinRate) * 0.9 * height);

    if (!location[x]) {
      location[x] = []
    }
    if (!location[x][y]) {
      location[x][y] = []
    }
    location[x][y].push(name);

    drawCard(context, x, y, cardInfo[name]);
  }

  canvas.onclick = function(event) {
    var canvasPos = findPos(canvas);
    var absX = event.clientX + document.body.scrollLeft + document.documentElement.scrollLeft;
    var absY = event.clientY + document.body.scrollTop + document.documentElement.scrollTop;

    var posX = absX - canvasPos[0];
    var posY = absY - canvasPos[1];

    var cards = [];
    for (var x = posX - 4; x <= posX + 4; x++) {
      for (var y = posY - 4; y <= posY + 4; y++) {
        if (location[x] && location[x][y]) {
          for (var i = 0; i < location[x][y].length; i++) {
            cards.push(location[x][y][i]);
          }
        }
      }
    }

    if (cards.length == 0) {
      return;
    }

    console.log(absX + "::" + absY + "  " + posX + "::" + posY + "  " + cards.join(", "));

    createPopup(posX + canvasPos[0] + 5, posY + canvasPos[1] + 5, cards.join(", "));
    return false;
  }
}

function drawCard(context, x, y, card) {
  context.beginPath();
  context.fillStyle = 'rgba(220, 220, 70, .8)';
  var cost = parseInt(card["Cost"]);
  if (card["Type"] == "World") {
    context.arc(x, y, cost + 2, 0, Math.PI*2, true);
    switch (card["Goods"]) {
      case "Novelty": context.fillStyle = 'rgba(0, 192, 255, .7)'; break;
      case "Rare": context.fillStyle = 'rgba(75, 38, 0, .7)'; break;
      case "Genes": context.fillStyle = 'rgba(75, 255, 0, .7)'; break;
      case "Alien": context.fillStyle = 'rgba(200, 200, 30, .7)'; break;
      default: context.fillStyle = 'rgba(75, 75, 75, .7)';
    }
  } else {
    var hor = cost + 1;
    var vert = hor * 1.5;
    context.moveTo(x, y - vert);
    context.lineTo(x + hor, y);
    context.lineTo(x, y + vert);
    context.lineTo(x - hor, y);
    context.lineTo(x, y - vert);
  }

  if (card["Military"] == "X"
      || (card["Type"] == "Development"
          && (parseInt(card["Strength"]) > 0 || card["Name"].indexOf("Imperium") > -1))) {
    context.strokeStyle = 'rgba(255, 0, 0, .8)';
  } else {
    context.strokeStyle = 'rgba(0, 0, 0, .8)';
  }

  context.closePath();
  context.fill();
  context.stroke();
}

function createPopup(x, y, text) {
  var popup = document.createElement("div");
  popup.appendChild(document.createTextNode(text));
  popup.style.position = "absolute";
  popup.style.left = x +"px";
  popup.style.top = y +"px";
  popup.style.zIndex = 5;
  popup.style.border = "1 px solid #666";
  popup.style.background = "#eee";
  popup.style.padding = "2px";
  document.body.appendChild(popup);

  setTimeout(function() {
    var old = document.onclick;
    document.onclick = function() {
      document.body.removeChild(popup);
      document.onclick = old;
      if (old) {
        old();
      }
    }
  }, 10);
}

function findPos(obj) {
	var curleft = 0, curtop = 0;

  if (obj.offsetParent) {
    do {
      curleft += obj.offsetLeft;
      curtop += obj.offsetTop;
    } while (obj = obj.offsetParent);
    return [curleft,curtop];
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