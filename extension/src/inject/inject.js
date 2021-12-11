chrome.extension.sendMessage({}, function(response) {
	var readyStateCheckInterval = setInterval(function() {
	if (document.getElementById('cm_cr_dp_d_write_review')) {
		clearInterval(readyStateCheckInterval);

		// Try to see if we have any existing results and display them
		retrieveAnalysis(getASINFromPage())
		var reviewDiv = document.querySelectorAll('[data-widget-name="cr-solicitation"]')[0]
		var analyzeDiv = reviewDiv.cloneNode(true);
		analyzeDiv.id = 'analyzer-div'
		analyzeDiv.querySelectorAll('[data-hook="solicitation-title"]')[0].textContent = "Analyze product reviews"
		analyzeDiv.querySelectorAll('[data-hook="share-your-thoughts-text"]')[0].textContent = "See commonly mentioned topics for this product"
		analyzeDiv.querySelectorAll('[data-hook="write-review-button"')[0].textContent = "Analyze"
		analyzeDiv.querySelectorAll('[data-hook="write-review-button"')[0].addEventListener('click', handleAnalyze)
		var parent = document.getElementById("reviewsMedley").firstChild.firstChild;
		parent.appendChild(analyzeDiv);

	}
	}, 10);
});

const handleAnalyze = async e => {
	// OnClick Handler for Analyze Button on DP
	e.preventDefault();

	forceAnalysis(getASINFromPage())
	console.log(getASINFromPage())
}

const retrieveAnalysis = async ASIN => {
	// POST request to initiate scrape + process step
	const url = 'http://localhost:5000/scrape';
	const options = {
	  method: 'POST',
	  headers: {
		'Accept': 'application/json',
		'Content-Type': 'application/json;charset=UTF-8'
	  },
	  body: JSON.stringify({
		"asin": ASIN
		})
	};
	
	fetch(url, options)
		.then(response => response.json())
		.then(data => showTopics(data));
};

const forceAnalysis = async ASIN => {
	const url = 'http://localhost:5000/scrape';
	const options = {
	  method: 'POST',
	  headers: {
		'Accept': 'application/json',
		'Content-Type': 'application/json;charset=UTF-8'
	  },
	  body: JSON.stringify({
		"asin": ASIN,
		"force": true
		})
	};
	
	fetch(url, options)
		.then(response => response.json())
		.then(data => showMessage(data));
};

const showTopics = async e => {
	if (e.hasOwnProperty("topics") && e.topics.length >= 1) {
		var analyzerDiv = document.getElementById("analyzer-div")
		analyzerDiv.appendChild(createTable(e["pretty_topics"]))
	}
}

const showMessage = async e => {
	var analyzerDiv = document.getElementById("analyzer-div")
	analyzerDiv.insertAdjacentText("Processing started... reload page after some time.")
}

function getASINFromPage() {
	return window.location.href.substring(window.location.href.indexOf('dp') + 3, window.location.href.indexOf('dp') + 13)
}

function createTable(tableData) {
	var table = document.createElement('table');
	var tableBody = document.createElement('tbody');
  
	tableData.forEach(function(rowData) {
	  var row = document.createElement('tr');
  
	  rowData.forEach(function(cellData) {
		var cell = document.createElement('td');
		cell.appendChild(document.createTextNode(cellData));
		cell.style.border = "1px solid #000";
		row.appendChild(cell);
	  });
  
	  tableBody.appendChild(row);
	});
  
	table.style.border = "1px solid #000";
	table.appendChild(tableBody);
	return table;
  }