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
	var new_img = new Image();
	new_img.src = 'images/' + img_ids[i] + '.png';
	imgs.push(new_img);
    }
}

function GuardFillText(context) {
    var fillText = function(a, b, c) { };
    if (context.fillText) {
	context.font = "12 px sans-serif";
	fillText = function(a, b, c) { context.fillText(a, b, c) };
    }
    return fillText;
}


NOVELTY = 'rgba(0, 192, 255, .6)';
RARE = 'rgba(120, 60, 00, .6)';
GENES = 'rgba(75, 255, 0, .6)';
ALIEN = 'rgba(200, 200, 30, .6)';
GRAY = 'rgba(75, 75, 75, .6)';

function cardColor(card) {
    switch (card["Goods"]) {
    case "Novelty": return NOVELTY;
    case "Rare": return RARE;
    case "Genes": return GENES;
    case "Alien": return ALIEN;
    }    

    switch (card["Name"]) {
    case "Free Trade Association":
    case "Consumer Markets":
	return NOVELTY; 
    case "Mining League":
    case "Mining Conglomerate":
    case "Mining Robots":
	return RARE;
    case "Galactic Genome Project":
    case "Genetics Lab":
    case "Pan-galactic League":
	return GENES; 
    case "Alien Tech Institute":
	return ALIEN;
    }
    return GRAY;
}


function RenderHomeworldGoalData(canvas_id, data) {
    LoadImages();
    window.onload = function() {
	var canvas = document.getElementById(canvas_id);
	var context = canvas.getContext('2d');
	var fillText = GuardFillText(context); 
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
		var base = y_coord(data[i].win_points);
		var height = base - pos;

		if (height > 0) {
		    context.fillRect(cur_x, pos, 2, height);
		} else {
		    var top = Math.max(0, pos + height)
		    context.fillRect(cur_x, top, 2, -height);
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

  // Compute scales.
  var maxProbability = Number.MIN_VALUE, minProbability = Number.MAX_VALUE;
  var maxWinRate = Number.MIN_VALUE, minWinRate = Number.MAX_VALUE;
      

  for (var name in data) {
    var card = data[name];
    maxProbability = Math.max(maxProbability, card["prob_per_card"]);
    minProbability = Math.min(minProbability, card["prob_per_card"]);
    maxWinRate = Math.max(maxWinRate, card["norm_win_points"]);
    minWinRate = Math.min(minWinRate, card["norm_win_points"]);
  }

  function toCanvasX(prob) {
      return parseInt(prob /
                      (maxProbability - minProbability) 
                      * width * 0.8);
  }

  function toCanvasY(rate) {
      return parseInt((0.1 * height) + (maxWinRate - rate) /
		      (maxWinRate - minWinRate) * 0.8 * height);
  }

  var namesByCost = [];
  for (name in data) {
      namesByCost.push(name);
  }
  namesByCost.sort(function(nameA, nameB) { 
	  return parseInt(cardInfo[nameA]['Cost']) < 
	      parseInt(cardInfo[nameB]['Cost']);
      });

  var lowestBand = minProbability * minWinRate;
  var highestBand = maxProbability * maxWinRate;
  var NUM_BANDS = 10;
  var DETAIL = 200;

  var fillText = GuardFillText(context);
  context.strokeStyle = 'rgba(120, 120, 120, .5)';
  context.fillStyle = 'rgba(120, 120, 120, .5)';
  context.textAlign = 'center';
  for (var i = 0; i < NUM_BANDS; ++i) {
      context.beginPath();

      var curBand = lowestBand + i * (highestBand - lowestBand) / NUM_BANDS;
      context.moveTo(toCanvasX(minProbability), 
		     toCanvasY(curBand / minProbability));
      for (var j = 0; j < DETAIL; ++j) {
	  var curProb = minProbability + 
	      j * (maxProbability - minProbability) / DETAIL;
	  var curWin = curBand / curProb;
	  context.lineTo(toCanvasX(curProb), toCanvasY(curWin));
      }
      context.stroke();
      var targetHeight = maxWinRate * .95;
      fillText(("" + curBand).substr(0, 4), 
	       toCanvasX(curBand / targetHeight), 
	       toCanvasY(targetHeight));
  }

  // Draw dots.
  for (var i = 0; i < namesByCost.length; ++i) {
    var name = namesByCost[i];
    card = data[name];
    x = toCanvasX(card["prob_per_card"]);
    y = toCanvasY(card["norm_win_points"]);
    if (!location[x]) {
      location[x] = []
    }
    if (!location[x][y]) {
      location[x][y] = []
    }
    location[x][y].push(name);

    drawCard(context, x, y, cardInfo[name]);
  }
  context.fillStyle = 'black';
  context.textAlign = 'start';
  for (var i = 0; i <= 10; ++i) {
      var cur = i * maxProbability / 10;
      var label = ("" + cur).substring(0, 4);
      fillText(label, toCanvasX(parseFloat(label)), height - 8);
  }

  for (var i = 0; i <= 10; ++i) {
      var cur = i * (maxWinRate - minWinRate) / 10 + minWinRate;
      var label = ("" + cur).substring(0, 4);
      fillText(label, 10, toCanvasY(parseFloat(label)));
  }

  canvas.onclick = function(event) {
    var canvasPos = findPos(canvas);
    var absX = (event.clientX + document.body.scrollLeft + 
		document.documentElement.scrollLeft);
    var absY = (event.clientY + document.body.scrollTop + 
		document.documentElement.scrollTop);

    var posX = absX - canvasPos[0];
    var posY = absY - canvasPos[1];

    var cardNames = [];
    for (var x = posX - 4; x <= posX + 4; x++) {
      for (var y = posY - 4; y <= posY + 4; y++) {
        if (location[x] && location[x][y]) {
          for (var i = 0; i < location[x][y].length; i++) {
            cardNames.push(location[x][y][i]);
          }
        }
      }
    }

    if (cardNames.length == 0) {
      return;
    }

    for (var i = 0; i < cardNames.length; ++i) {
	// variance bars!
	var card = data[cardNames[i]];
	var x = toCanvasX(card["prob_per_card"]);
	var y = toCanvasY(card["norm_win_points"]);
	var twoYDevs = 2 * card["norm_win_points_ssd"];
	var yDevMax = toCanvasY(card["norm_win_points"] - twoYDevs);
	var yDevMin = toCanvasY(card["norm_win_points"] + twoYDevs);
	context.beginPath();
	context.strokeStyle = cardColor(cardInfo[cardNames[i]]);
	context.moveTo(x - 5, yDevMax);
	context.lineTo(x + 5, yDevMax);
	context.moveTo(x - 5, yDevMin);
	context.lineTo(x + 5, yDevMin);
	context.moveTo(x, yDevMin);
	context.lineTo(x, yDevMax);
	context.stroke();
    }
    
    createPopup(posX + canvasPos[0] + 5, posY + canvasPos[1] + 5, 
		cardNames.join(", "));
    return false;
  }
}

function drawCard(context, x, y, card) {
  context.beginPath();
  var renderSize = parseInt(card["Cost"]) + 2;
  cardCol = cardColor(card)
  context.fillStyle = cardCol;
  if (card["Type"] == "World") {
    context.arc(x, y, renderSize + 2, 0, Math.PI*2, true);
  } else {
    var hor = renderSize + 1;
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
    context.strokeStyle = 'rgba(255, 0, 0, 1.0)';
  } else {
    context.strokeStyle = 'rgba(0, 0, 0, 1.0)';
  }

  context.closePath();
  context.fill();
  context.stroke();

  if (card["Production"] == "Windfall") {
      context.beginPath();
      context.arc(x, y, renderSize / 2, 0, Math.PI * 2, true);
      context.fillStyle = 'rgba(255, 255, 255, 1.0)';
      context.closePath();
      context.fill();
      context.stroke();
  }
  
  context.closePath();
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
