chrome.extension.sendMessage({}, function(response) {
	var readyStateCheckInterval = setInterval(function() {
	if (document.getElementById('cm_cr_dp_d_write_review')) {
		clearInterval(readyStateCheckInterval);

		var button = document.createElement("button");
		button.className = "";
		button.textContent = "Analyze Reviews";
		button.addEventListener('click', handleAnalyze);
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

const retrieveAnalysis = async ASIN => {
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

const handleAnalyze = async e => {
	var ASIN = window.location.href.substring(window.location.href.indexOf('dp') + 3, window.location.href.indexOf('dp') + 13)
	e.preventDefault();
	retrieveAnalysis(ASIN)
	console.log(ASIN)
}

const showTopics = async e => {
	var analyzerDiv = document.getElementById("analyzer-div")
	analyzerDiv.insertAdjacentText("afterEnd", e["topics"])
}