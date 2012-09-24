var img_ids_num = 20;
// img_ids_num needs to be set for this script to work, eg
// var img_ids_num = 10
// for tgs.  It is automatically set in compute_stats.py to the correct value before
// being copied over to the output directory

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
	       "alien",
	       "explore",
	       "rebel",
	       "4goods",
	       "8tableau",
	       "3uplift",
	       "consume",
	       "prestige",
	       "2prestige3vp",
	       "peacewar",
	       "militaryinfluence"
	       ];
var imgs = [];

var homeworld_colors = {'Alpha Centauri': '#663300',
			'Epsilon Eridani': '#9900FF',
			'Old Earth': '#000099',
			'Ancient Race': '#00FF00',
			'Damaged Alien Factory': '#FFFF00',
			"Earths Lost Colony": '#00CCFF',
			'New Sparta': '#FF0000',
			'Separatist Colony': '#555555',
			'Doomed World': '#000000',
                        'Imperium Warlord': '#AA00AA',
                        'Rebel Cantina': '#FF5555',
                        'Galactic Developers': '#FF00FF',
			'Rebel Freedom Fighters': '#FF0055',
			'Uplift Mercenary Force': '#66FF00',
			'Galactic Scavengers': '#0099FF',
			'Alien Research Team': '#FFFF55'
};

function LoadImages() {
    for (var i = 0; i < img_ids_num; ++i) {
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

function rgbaToRgb(rgbaStr) {
    return rgbaStr.replace('rgba', 'rgb').replace(/(.*),(.*),(.*),(.*)\)/, 
						  "$1,$2,$3)");
}

DEFAULT_ALPHA = 0.6;

function cardColor(card, alpha) {
    if (alpha == null) {
	alpha = DEFAULT_ALPHA;
    }
    var NOVELTY = '0, 192, 255';
    var RARE = '120, 60, 0';
    var GENES = '75, 255, 0';
    var ALIEN = '200, 200, 30';
    var GRAY = '75, 75, 75';

    var colorTupleWithoutAlpha = function(card) {
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
	case "Prospecting Guild":
	case "Mining League":
	case "Mining Conglomerate":
	case "Mining Robots":
	return RARE;
	case "Galactic Genome Project":
	case "Genetics Lab":
	case "Pan Galactic League":
	case "Uplift Code":
	return GENES; 
	case "Alien Tech Institute":
	return ALIEN;
	}
	return GRAY;
    }
    return 'rgba(' + colorTupleWithoutAlpha(card) + ',' + alpha + ')';
}

function strokeColor(card, alpha) {
    if (alpha == null) alpha = 1.0;
    function colorTupleWithoutAlpha(card) {
	var RED = '255, 0, 0';
	var PURPLE = '192, 0, 192';
	var BLACK = '0,0,0';
	if (card["Military"] == "X") {
	    return RED;
	} 
	if (card["Name"].indexOf("Imperium") > -1) {
	    return PURPLE;
	}
	if (card["Type"] == "Development") {
	    if (parseInt(card["Strength"]) > 0) {
		return RED;
	    }
	    if (card["Name"].indexOf("Rebel") > -1) {
		return RED;
	    }
	}
	return BLACK;
    }
    return 'rgba(' + colorTupleWithoutAlpha(card) + ',' + alpha + ')';
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

	var MAX_RATE = 1.4;
	var MIN_RATE = 0.6;
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
	    fillText(hw, canvas.width - 200, (i + 1) * 20 + 150 - (data.length/2*20) + 90);

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

function WindowBound(width, height) {
    var bound = {}
    bound.width = width;
    bound.height = height;
    bound.maxProbability = Number.MIN_VALUE;
    bound.minProbability = Number.MAX_VALUE;
    bound.maxWinRate = Number.MIN_VALUE;
    bound.minWinRate = Number.MAX_VALUE;

    bound.ExtendToFit = function(cardWinData) {
	for (var name in cardWinData) {
	    var card = cardWinData[name];
	    bound.maxProbability = Math.max(bound.maxProbability, 
					   card["prob_per_card"]);
	    bound.minProbability = Math.min(bound.minProbability, 
					   card["prob_per_card"]);
	    bound.maxWinRate = Math.max(bound.maxWinRate, 
					card["norm_win_points"]);
	    bound.minWinRate = Math.min(bound.minWinRate, 
					card["norm_win_points"]);
	};
    };

    bound.ToCanvasX = function(prob) {
	return parseInt(prob / (bound.maxProbability - bound.minProbability) * 
			bound.width * 0.8);
    };

    bound.ToCanvasY = function(rate) {
	return parseInt((0.1 * bound.height) + (bound.maxWinRate - rate) /
			(bound.maxWinRate - bound.minWinRate) * 0.8 * height);
    }
    return bound;
};

function RenderCardWinInfo(data, canvas, wind, alphaPerCard) {
    if (!alphaPerCard) {
	alphaPerCard = {}
    }
    var context = canvas.getContext("2d"), 
	height = canvas.height, 
	width = canvas.width,
	location = [], card, x, y;

    var window = wind;
    if (!window) {
	window = WindowBound(width, height);
    }
    window.ExtendToFit(data);

    context.clearRect(0, 0, width, height);

    var minP = Math.max(window.minProbability, .01);
    var lowestBand = minP * window.minWinRate;
    var highestBand = window.maxProbability * window.maxWinRate;
    var NUM_BANDS = 10;
    var DETAIL = 200;

    var fillText = GuardFillText(context);
    context.strokeStyle = 'rgba(120, 120, 120, .5)';
    context.fillStyle = 'rgba(120, 120, 120, .5)';
    context.textAlign = 'center';
    for (var i = 0; i < NUM_BANDS; ++i) {
	context.beginPath();

	var curBand = lowestBand + i * (highestBand - lowestBand) / NUM_BANDS;

	var x = window.ToCanvasX(minP);
	var y = window.ToCanvasY(curBand / minP);
	context.moveTo(x, y);
		       
	for (var j = 0; j < DETAIL; ++j) {
	    var curProb = minP + j * (window.maxProbability - minP) / DETAIL;
	    var curWin = curBand / curProb;
	    context.lineTo(window.ToCanvasX(curProb), 
			   window.ToCanvasY(curWin));
	}
	context.stroke();
	var targetHeight = window.maxWinRate * .95;
	fillText(("" + curBand).substr(0, 4), 
		 window.ToCanvasX(curBand / targetHeight), 
		 window.ToCanvasY(targetHeight));
    }

    for (var i = 0; i <= 10; ++i) {
	var cur = i * window.maxProbability / 10;
	var label = ("" + cur).substring(0, 4);
	fillText(label, window.ToCanvasX(parseFloat(label)), height - 8);
    }

    for (var i = 0; i <= 10; ++i) {
	var cur = i * (window.maxWinRate - window.minWinRate) / 10 + 
	    window.minWinRate;
	var label = ("" + cur).substring(0, 4);
	fillText(label, 10, window.ToCanvasY(parseFloat(label)));
    }

    var namesByCost = [];
    for (name in data) {
	namesByCost.push(name);
    }
    namesByCost.sort(function(nameA, nameB) { 
	    return parseInt(cardInfo[nameA]['Cost']) -
		parseInt(cardInfo[nameB]['Cost']);
	});

    // Draw dots.
    for (var i = 0; i < namesByCost.length; ++i) {
	var name = namesByCost[i];
	card = data[name];
	x = window.ToCanvasX(card["prob_per_card"]);
	y = window.ToCanvasY(card["norm_win_points"]);
	if (!location[x]) {
	    location[x] = [];
	}
	if (!location[x][y]) {
	    location[x][y] = [];
	}
	location[x][y].push(name);
	drawCard(context, x, y, cardInfo[name], alphaPerCard[name],
		 alphaPerCard[name]);
    }
    context.fillStyle = 'black';
    context.textAlign = 'start';

    canvas.onclick = function(event) {
	RenderCardWinInfo(data, canvas, window);
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
	    var x = window.ToCanvasX(card["prob_per_card"]);
	    var y = window.ToCanvasY(card["norm_win_points"]);
	    
	    var twoXDevs = 2 * card["prob_per_card_ssd"];
	    var xDevMin = window.ToCanvasX(card["prob_per_card"] - twoXDevs);
	    var xDevMax = window.ToCanvasX(card["prob_per_card"] + twoXDevs);

	    var twoYDevs = 2 * card["norm_win_points_ssd"];
	    var yDevMax = window.ToCanvasY(card["norm_win_points"] - twoYDevs);
	    var yDevMin = window.ToCanvasY(card["norm_win_points"] + twoYDevs);

	    // hack.  It seems like the lines are drawn half transparent the 
	    // first time, drawing them over and over gets rid of the effect.
	    context.strokeStyle = rgbaToRgb(cardColor(cardInfo[cardNames[i]]));
	    for (var j = 0; j < 5; ++j) {
		context.beginPath();
		context.moveTo(x - 5, yDevMax);
		context.lineTo(x + 5, yDevMax);
		context.moveTo(x - 5, yDevMin);
		context.lineTo(x + 5, yDevMin);
		context.moveTo(x, yDevMin);
		context.lineTo(x, yDevMax);
		context.stroke();

		context.beginPath();
		context.moveTo(xDevMin, y + 5);
		context.lineTo(xDevMin, y - 5);
		context.moveTo(xDevMax, y + 5);
		context.lineTo(xDevMax, y - 5);
		context.moveTo(xDevMin, y);
		context.lineTo(xDevMax, y);
		context.stroke();
	    }
	}
    
	createPopup(posX + canvasPos[0] + 5, posY + canvasPos[1] + 5, 
		    cardNames.join(", "));
	return false;
    }
}

function VectorMul(v, mul) {
    var ret = {};
    for (var key in v) {
	ret[key] = v[key] * mul;
    }
    return ret;
}

function VectorAdd(a, b) {
    var ret = {};
    if (a.length != b.length) {
	throw "mismatched lengths " + a.length + " " + b.length;
    }
    for (var key in a) {
	if (!(key in b)) {
	    throw key + " missing";
	}
	ret[key] = a[key] + b[key];
    }
    return ret;
}

function CombineFrame(loFrameData, hiFrameData, interp) {
    if (loFrameData != null && hiFrameData != null) {
	return VectorAdd(VectorMul(loFrameData, 1 - interp),
			 VectorMul(hiFrameData, interp));
    }
    if (loFrameData != null) return loFrameData;
    return hiFrameData;
}

function LinearInterp(x, low, high) {
    return x * low + (1 - x) * high;
}

function CalculateFade(loFrameData, hiFrameData, interp) {
    var interp = interp * 5 - 4;
    if (interp < 0) interp = 0;
    if (loFrameData != null && hiFrameData != null) return DEFAULT_ALPHA;
    if (loFrameData != null) return LinearInterp(interp, 0, DEFAULT_ALPHA);
    return LinearInterp(1 - interp, 0, DEFAULT_ALPHA);
}

function CardDataAnimation(divId) {
    var animator = {};
    var containingDiv = document.getElementById(divId);
    var stopButtonId = divId + 'Stop';
    var startButtonId = divId + 'Start';
    containingDiv.innerHTML = '<table><tr><td>Winning Rate</td>' +
	'<td><canvas id="cardWinAnimationCanvas" height="600" width="800">' +
	'</canvas></td></tr>' + 
	'<tr>' + 
	'<td></td><td><center>' +
	'Probability instance of card appears on tableau</center></td>' + 
	'</tr>' +
	'<tr><td><input type="button" value="Stop" id=' + stopButtonId + '>' +
	'</input></td>' +
	'<td>' + 
	'</tr><input type="button" value="Start" id=' + startButtonId + '>'
	'</table>';
    document.getElementById(stopButtonId).onclick = function() { 
	animator.Stop();
    }
    document.getElementById(stopButtonId).onclick = function() { 
	animator.Start();
    }
    animator.Stop = function() {
	clearInterval(animator.interval);
    }
    animator.Start = function() {
	// make graph interuptible.  the key state is in elapsed, pretty much
	// everything else is derivable from that.  
    }
    animator.Render = function(animInfo) {
	var canvas = document.getElementById('cardWinAnimationCanvas');
	var duration = 15000;
	var start = new Date().getTime();
	var window = WindowBound(canvas.width, canvas.height);
	for (var i = 0; i < animInfo.length; ++i) {
	    window.ExtendToFit(animInfo[i].data);
	}
	var doneNext = false;
	animator.interval = setInterval(function() {
		var now = new Date().getTime();
		var elapsed = now - start;
		//console.log(elapsed);
		var loFrame = Math.floor(elapsed / duration);
		var hiFrame = loFrame + 1;
		var interp = elapsed / duration - loFrame;
		if (hiFrame >= animInfo.length) {
		    if (!doneNext) {
			loFrame = hiFrame = animInfo.length - 1;
			doneNext = true;
		    }
		    else {
			return;
		    }
		}
		var sInterp = interp * interp * (3 - 2 * interp);
		var interpData = {};
		var transparency = {}
		// Should really do a union of the keys and iterate over that.
		for (var cardName in animInfo[hiFrame].data) {
		    loFrameCardData = animInfo[loFrame].data[cardName];
		    hiFrameCardData = animInfo[hiFrame].data[cardName];

		    interpData[cardName] = CombineFrame(loFrameCardData,
							hiFrameCardData,
							sInterp);
		    transparency[cardName] = CalculateFade(loFrameCardData,
							   hiFrameCardData,
							   sInterp);
								   
		}
		RenderCardWinInfo(interpData, canvas, window, transparency);

		var ctx = canvas.getContext('2d');
		var fillText = GuardFillText(ctx);
		function RenderInterpBar(title, x, y, interpVal) {
		    fillText(title, x, y);
		    var barWidth = canvas.width * interpVal / 10;
		    ctx.fillRect(x - barWidth, y - 5,
				 barWidth, 10);
		}
		for (var i = 0; i < animInfo.length; ++i) {
		    var interpVal = 0.0;
		    if (i == loFrame) interpVal = 1 - sInterp;
		    else if (i == hiFrame) interpVal = sInterp;
		    RenderInterpBar(animInfo[i].title, 
				    canvas.width * 8 / 10, 
				    canvas.height * 4/5 + 20 * i, 
				    interpVal);
		}
	    }, 50);
    }    
    return animator;
}

function drawCard(context, x, y, card, fillAlpha, strokeAlpha) {
  context.beginPath();
  var renderSize = parseInt(card["Cost"]) + 2;
  cardCol = cardColor(card, fillAlpha);
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

  context.strokeStyle = strokeColor(card, strokeAlpha);

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

function Matrix(elems) {
    var self = {};
    if (elems) {
	self.elems = elems;
	if (elems.length != 3) {
	    alert("bad first dimension " + elems.length);
	}
	for (var i = 0; i < 3; ++i) {
	    if (elems[i].length != 3) {
		alert("bad second dimension " + elems[i].length);
	    }
	}
    } else {
	self.elems = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
    }
    self.Copy = function() {
	var cpElems = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
	for (var i = 0; i < 3; ++i) {
	    for (var j = 0; j < 3; ++j) {
		cpElems[i][j] = self.elems[i][j];
	    }
	}
	return Matrix(cpElems);
    }

    return self;
}

function RotatationMatrix(angle) {
    var cos_theta = cos(theta);
    var sin_theta = sin(theta);
    return Matrix([[cos_theta, -sin_theta, 0],
		   [sin_theta, cos_theta, 0, 0],
		   [0, 0, 1]]);
}

function TranslationMatrix(x, y) {
    return Matrix([[1, 0, x],
		   [0, 1, y],
		   [0, 0, 1]]);
}

function ScaleMatrix(sx, sy) {
    return Matrix([[sx, 0, 0],
		   [0, sy, 0],
		   [0,  0, 1]]);
}

function IdentityMatrix() {
    return Matrix([[1, 0, 0],
		   [0, 1, 0],
		   [0, 0, 1]]);
}

function MatrixMult(a, b) {
    var ret = Matrix();
    for (var i = 0; i < 3; ++i) {
	for (var j = 0; j < 3; ++j) {
	    for (var k = 0; k < 3; ++k) {
		ret.elems[i][j] += a.elems[i][k] * b.elems[k][j];
	    }
	}
    }
    return ret;
}

function MatrixVecMult(mat, v) {
    var ret = [0, 0, 0];
    for (var i = 0; i < 3; ++i) {
	for (var j = 0; j < 3; ++j) ret[i] += mat.elems[i][j] * v[j];
    }
    return ret;
}

function MyContext(ctx) {
    var myCtx = {};
    myCtx.modelMats = [IdentityMatrix()];
    
    myCtx.curModelMat = function() {
	return myCtx.modelMats[myCtx.modelMats.length - 1];
    }

    myCtx.save = function() {
	myCtx.modelMats.push(myCtx.curModelMat().Copy());
    };

    myCtx.restore = function() {
	myCtx.modelMats.pop();
    }

    myCtx.modelToScreen = function(x, y) {
	var ret = MatrixVecMult(myCtx.curModelMat(), [x, y, 1]);
	if (ret[0] < 0) ret[0] = 0;
	if (ret[1] < 0) ret[1] = 0;
	return ret;
    }

    myCtx.drawLine = function(x1, y1, x2, y2) {
	var first = myCtx.modelToScreen(x1, y1);
	var second = myCtx.modelToScreen(x2, y2);
	ctx.beginPath();
	ctx.moveTo(first[0], first[1]);
	ctx.lineTo(second[0], second[1]);
	ctx.stroke();
	ctx.closePath();
    }
    myCtx.fillRect = function(x, y, w, h) {
	var first = MatrixVecMult(myCtx.curModelMat(), [x, y, 1]);
	var other_corner = MatrixVecMult(myCtx.curModelMat(), 
					 [x + w, y + h, 1]);
	var new_w = other_corner[0] - first[0];
	var new_h = other_corner[1] - first[1];
	ctx.fillRect(first[0], first[1], new_w, new_h);
    }
    myCtx.translate = function(x, y) {
	var nextMat = MatrixMult(myCtx.curModelMat(), TranslationMatrix(x, y));
	myCtx.modelMats[myCtx.modelMats.length - 1] = nextMat;
    }
    myCtx.scale = function(x, y) {
	var nextMat = MatrixMult(myCtx.curModelMat(), ScaleMatrix(x, y));
	myCtx.modelMats[myCtx.modelMats.length - 1] = nextMat;
    }

    var fillText = GuardFillText(ctx);
    myCtx.fillText = function(text, x, y) {
	var screenCoords = myCtx.modelToScreen(x, y);
	fillText(text, screenCoords[0], screenCoords[1]);
    }
    
    return myCtx;
}

function PointDistribution(divId) {
    var elem = document.getElementById(divId);
    elem.innerHTML = '<h2>Point score distribution for six cost ' + 
	'developments</h2>' +
	'<p>I have collected data about the actual and potential score ' +
	'of all of the six cost developments in Race from ' +
	'many completed games on Genie or Flex. I did this in hopes of ' +
	'gaining some ' +
	'insight into the nature of the game, and in particular, ' +
	'the cost 6 developments ' +
	'which tend to be the cornerstone of many strategies. '+
	'<p>The score distribution for each six cost development in the ' +
	'Race is summarized below. Each six cost development has ' +
	'a pair of whisker plots for the point distribution when the dev ' +
	'was played, and for how it would have scored on tableaus in which ' +
	'it was not played.  The distributions are clickable to get the ' +
	'card name and summary statistics.  The whisker plots contain ' +
	'a mean ' +
	'near the 5th, 25th, 50th, 75, and 95th percentile scores. ' +
	'A table including all of the summary stats is below.<br>' +
	'<p>Thanks to Edward Fu (<a href="player_theory.html">theory</a>), ' +
	'Alex Chen (<a href="player_vivafringe.html">vivafringe</a>), and ' +
	'Larry Mak (<a href="player_Larry.html">Larry</a>) ' +
	'for inspiration, ideas, and refinements to this page.' +
	'<table><tr><td>Point<br>distribution</td>' +
	'<td><canvas id="pointDistCanvas" height="500" width="1000">' +
	'</canvas></td></tr>' + 
	'<tr>' + 
	'<td></td><td><center>' +
	'Probability* instance of card appears on tableau<br>' +
	'<font size=-1>*some bars shifted right to avoid overdraw</font>' +
	'</center></td>' + 
	'</tr></table><div id="pointDistTable">';

    var canvas = document.getElementById("pointDistCanvas");
    var ctx = canvas.getContext('2d');
    var myCtx = MyContext(ctx);

    var whiskerWidth = .0015;

    var ret = {}
    var screenXToCardName = [];

    ret.Render = function(pointData) {
	var maxDesireX = 0.0;
	var maxDesireY = 20;
	var minDesireX = -.01;
	var minDesireY = -1;

	for (cardName in pointData) {
	    maxDesireX = Math.max(maxDesireX, pointData[cardName].played.prob);
	}
	maxDesireX *= 1.05;

	var xRange = maxDesireX - minDesireX;
	var yRange = maxDesireY - minDesireY;

	myCtx.scale(canvas.width / xRange, -canvas.height / yRange);
	myCtx.translate(-minDesireX, -maxDesireY);

	var pointDataOrder = [];
	for (cardName in pointData) {
	    pointDataOrder[pointDataOrder.length] = cardName;
	}
	pointDataOrder.sort(function(x, y) { 
		return pointData[x].played.prob - pointData[y].played.prob; 
	    });

	function RenderSingleCardToHtml(cardName) {
	    function round(v, prec) {
		if (!prec) {
		    prec = 4;
		}
		var ret = "" + v;
		return ret.substr(0, prec);
	    }
	    var cardData = pointData[cardName];
	    return '<tr><td>' + cardName + '</td>' + 
		    '<td>' + round(cardData.played.mean) + ' +- ' +
		    round(cardData.played.stdDev * 2) + '</td>' +
		    '<td>' + round(cardData.unplayed.mean) + ' +- ' +
		    round(cardData.unplayed.stdDev * 2) + '</td>' +
		    '<td>' + round(cardData.played.prob, 5) + '</td>' +
		    '</tr>';
	}

	var summaryTableHeader = '<table border=1><tr>' +
		'<td>Card Name</td>' +
		'<td>Played Mean +- 2 Std Dev</td>' +
	        '<td>Unplayed Mean +- 2 Std Dev</td>' +
		'<td>Play Prob</td>' + 
	'</tr>';

	function RenderSummaryDataToTable() {
	    var dataSummaryHtml = summaryTableHeader;
	    for (var i = pointDataOrder.length - 1; i >= 0; i--) {
		dataSummaryHtml += RenderSingleCardToHtml(pointDataOrder[i]);
	    }
	    dataSummaryHtml += '</table>';
	    return dataSummaryHtml;
	}
	var pointTableDiv = document.getElementById('pointDistTable');
	pointTableDiv.innerHTML = RenderSummaryDataToTable();


	myCtx.drawLine(0, 0, maxDesireX, 0);
	myCtx.drawLine(0, 0, 0, maxDesireY);
	for (var i = 2; i < maxDesireY; i += 2) {
	    ctx.strokeStyle = "rgba(0, 0, 0, 0.0)";
	    myCtx.fillText(i, minDesireX/2, i);	 
	    ctx.strokeStyle = "rgba(210, 210, 210, 1.0)";   
	    myCtx.drawLine(0, i, maxDesireX, i);	 
	}
	for (var i = .02; i < maxDesireX; i += .02) {
	    var xLabel = ("" + (i + .0001)).substr(0, 4);
	    var xPos = parseFloat(xLabel);
	    myCtx.fillText(xLabel, xPos, minDesireY/2);	    
	}

	function RenderBoxPlot(boxPlotData) {
	    var s = boxPlotData.summary;

	    myCtx.fillRect(0, s[1], whiskerWidth/2, s[3] - s[1]);

	    myCtx.drawLine(0, s[0], 0, s[1]);
	    myCtx.drawLine(0, s[3], 0, s[4]);

	    myCtx.drawLine(0, s[1], 0, s[s.length - 2]);
	    myCtx.drawLine(whiskerWidth/2, s[1], whiskerWidth/2, 
			   s[s.length - 2]);

	    for (var i = 0; i < boxPlotData.summary.length; ++i) {
		var x1 = 0;
		var x2 = whiskerWidth;
		if (0 < i && i < 4) {
		    x2 /= 2;
		}
		var y = boxPlotData.summary[i];
		myCtx.drawLine(x1, y, x2, y);
	    }
	}

	var lastX = 0;
	for (var i = 0; i < pointDataOrder.length; ++i) {
	    var cardName = pointDataOrder[i];
	    ctx.strokeStyle = strokeColor(cardInfo[cardName]);
	    ctx.fillStyle = cardColor(cardInfo[cardName]);

	    var curX = pointData[cardName].played.prob;
	    if (curX < lastX + 3 * whiskerWidth) {
		curX = lastX + 3 * whiskerWidth;
	    }
	    myCtx.save();
	    myCtx.translate(curX, 0);
	    RenderBoxPlot(pointData[cardName].played);
	    screenXToCardName.push([myCtx.modelToScreen(0, 0)[0],
				    cardName]);
	    myCtx.scale(-1, 1);
	    RenderBoxPlot(pointData[cardName].unplayed);
	    myCtx.restore();
	    lastX = curX;
	}
	canvas.onclick = function(event) {
	    //ret.Render(pointData);
	    var canvasPos = findPos(canvas);
	    var absX = (event.clientX + document.body.scrollLeft + 
			document.documentElement.scrollLeft);
	    var absY = (event.clientY + document.body.scrollTop + 
			document.documentElement.scrollTop);
	    var posX = absX - canvasPos[0];
	    var posY = absY - canvasPos[1];
	    minDist = 30;
	    var cardName = "";
	    for (var i = 0; i < screenXToCardName.length; ++i) {
		var curDist = Math.abs(posX - screenXToCardName[i][0]);
		if (curDist < minDist) {
		    minDist = curDist;
		    cardName = screenXToCardName[i][1];
		}
	    }
	    if (minDist < 30) {
		createPopup(posX + canvasPos[0], posY + canvasPos[1], 
			    summaryTableHeader + 
			    RenderSingleCardToHtml(cardName) +
			    '</table>');
	    }
	}
    };
    return ret
};

function createPopup(x, y, text) {
  var popup = document.createElement("div");
  popup.innerHTML = text;
  // popup.appendChild(document.createTextNode(text));
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
