/*
 * For Android.
 * Most of the implementations are in Java.
 * Some override the JavaScript interface directly.
 */

/**
 * Send an API request to Java.
 */
internal.priv.send = function(data) {
	if (window['__forge']['callJavaFromJavaScript'] === undefined) {
		// Java should have added "callJavaFromJavaScript" but it hasn't?
		return;
	}
	
	var paramsAsJSON = ((data.params !== undefined) ? JSON.stringify(data.params) : "");
	
	window['__forge']['callJavaFromJavaScript'](data.callid, data.method, paramsAsJSON);
};

// Let Java know we're ready.
internal.priv.send({callid: "ready", method: ""});

/**
 * Expose method for Java to talk to JS
 */
forge['_receive'] = internal.priv.receive;
