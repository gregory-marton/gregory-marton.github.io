var containersToFill = [];

function reAddDefinition(cardinfo, container) {
    var dt = document.createElement("dt");
    dt.innerHTML = cardinfo.date;
    container.appendChild(dt);
    var dd = document.createElement("dd");
    dd.innerHTML = cardinfo.body;
    container.appendChild(dd);
}

function addCardToColumn(cardinfo, column) {
    card = document.createElement("div");
    card.className = "row card";
    column.appendChild(card);

    var bodySegment = document.createElement("div");
    bodySegment.className = "col card-body s12";
    card.appendChild(bodySegment);

    var dateSegment = document.createElement("div");
    dateSegment.className = "card-date";
    dateSegment.innerHTML = cardinfo.date;
    bodySegment.appendChild(dateSegment);

    for (var f = 0; f < cardinfo.featured.length; f++) {
	      var image = document.createElement("img");
	      image.src = cardinfo.featured[f].img;
	      image.className = "card-feature-image";
	      if (cardinfo.featured[f].uri) {
	          var link = document.createElement("a");
	          link.href = cardinfo.featured[f].uri;
	          link.className = "card-feature-link";
	          link.appendChild(image);
	          bodySegment.appendChild(link);
	      } else {
	          bodySegment.appendChild(image);
	      }
    }
    
    var parSegment = document.createElement("p");
    parSegment.innerHTML = cardinfo.body;
    bodySegment.appendChild(parSegment);
}

function fillWithCards(container_id, cardWidth, cardPadding) {
    var container = document.getElementById(container_id);
    
    var lastDate = "";
    var cards = [];
    while (container.firstChild) {
	var child = container.firstChild;
        if (child.tagName == "DT") {
            // Remember the date.
            lastDate = child.innerHTML;
	} else if (child.tagName == "DD") {
	    // Make a card.
	    cardinfo = {date: lastDate, featured: []};
	    cardinfo.body = child.innerHTML;
	    links = child.getElementsByTagName("a");
	    for (var l = 0; l < links.length; l++) {
		var link = links[l];
		if (link.hasAttribute("img")) {
		    src = link.getAttribute("img");
		    cardinfo.featured.push({img: src, uri: link.href});
		}
	    }
	    cards.push(cardinfo);
	}
	container.removeChild(container.firstChild);
    }
    containersToFill.push({box: container, cards: cards,
			   cardWidth: cardWidth, cardPadding: cardPadding});
}

function createLayouts() {
    for (var container_id = 0; container_id < containersToFill.length;
         container_id++) {
        container_data = containersToFill[container_id];
	      var container = container_data.box;
	      var cards = container_data.cards;
	      var cardWidth = container_data.cardWidth;
	      var cardPadding = container_data.cardPadding;
	      var width = container.offsetWidth;
	      while (container.lastChild) {
	          container.removeChild(container.lastChild);
	      }
	      
	      columns = [];
	      var numColumns = Math.floor(width / (cardWidth + 2 * cardPadding));
	      var padding = Math.floor((width -
				                          numColumns * (cardWidth + cardPadding)) /
				                         (2 * numColumns));
	      for (var i = 0; i < numColumns; i++) {
	          var column = document.createElement("div");
	          column.className = "cards-column";
	          column.style.position = "relative";
	          column.style.left = padding * (1 + i) + "px";
	          columns.push(column);
	          container.appendChild(column);
	      }
	      if (columns.length > 0) {
	          for (var i = 0; i < cards.length; i++) {
		            var min_col;
		            var min_height = Math.pow(2, 32);
		            for (var c = 0; c < columns.length; c++) {
		                if (columns[c].offsetHeight < min_height) {
			                  min_height = columns[c].offsetHeight;
			                  min_col = c;
		                }
		            }
		            addCardToColumn(cards[i], columns[min_col])
	          }
	      } else {
	          // No space for cards, just add the text back.
	          for (var i = 0; i < cards.length; i++) {
		            reAddDefinition(cards[i], container)
	          }
	      }	    
    }
}


window.onresize = createLayouts;
