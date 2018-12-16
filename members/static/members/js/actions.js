function deletePerson(url, callerElement, name) {
	// Be asure of the deletion
	if (confirm("Er du sikker på, at du vil slette '" + name + "'")) {
		// Send delete request to server
		var xhr = new XMLHttpRequest();
		var json = JSON.stringify({ "action": "delete" });
		xhr.open("POST", url);
		xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
		xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));

		// Perform when request has finished
		xhr.onreadystatechange = function () { // Call a function when the state changes.
			if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
				// If success, then remove person in local front-end; if not success, give an error
				if (this.responseText == "Success") {
					deleteRow(callerElement);
				} else {
					alert(this.responseText);
				}
			}
		};
		// Do the request
		xhr.send(json);
	}
}

function getCookie(name) {
	if (!document.cookie) {
		return null;
	}

	const xsrfCookies = document.cookie.split(';')
		.map(c => c.trim())
		.filter(c => c.startsWith(name + '='));

	if (xsrfCookies.length === 0) {
		return null;
	}

	return decodeURIComponent(xsrfCookies[0].split('=')[1]);
}

function deleteRow(childElement) {
	// Go upwards until the hit of the row element
	while (childElement.tagName != "TR") {
		childElement = childElement.parentNode;
	}

	// Delete itself (itself = row)
	childElement.parentNode.removeChild(childElement);
}