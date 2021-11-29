/* global internal, forge */

/*
 * iOS specific code
 */

var temporaryNativeQueueStorage = [];
var hasLoaded = false;

internal.priv.get = function () {
    var curData = JSON.stringify(temporaryNativeQueueStorage);
    temporaryNativeQueueStorage = [];
    return curData;
};

var timeouts = [],
    messageName = 'zero-timeout-message';

// Like setTimeout, but only takes a function argument.  There's
// no time argument (always zero) and no arguments (you have to
// use a closure).
function setZeroTimeoutPostMessage(fn) {
    timeouts.push(fn);
    window.postMessage(messageName, '*');
}

function setZeroTimeout(fn) {
    setTimeout(fn, 0);
}

function handleMessage(event) {
    if (event.source == window && event.data == messageName) {
        if (event.stopPropagation) {
            event.stopPropagation();
        }
        if (timeouts.length) {
            timeouts.shift()();
        }
    }
}

if (window.postMessage) {
    if (window.addEventListener) {
        window.addEventListener('message', handleMessage, true);
    } else if (window.attachEvent) {
        window.attachEvent('onmessage', handleMessage);
    }
    window.setZeroTimeout = setZeroTimeoutPostMessage;
} else {
    window.setZeroTimeout = setZeroTimeout;
}


internal.priv.send = function(data) {
    if (hasLoaded) {
        window.webkit.messageHandlers.forge.postMessage(data);
    } else {
        console.log("Forge API's are only available once all content has loaded.\n");
        console.log("Consider using: document.addEventListener(\"DOMContentLoaded\", function(event) { ... do stuff });");
    }
};

document.addEventListener("DOMContentLoaded", function () {
    hasLoaded = true;
    forge.internal.call("internal.ping", {data: "hello"});
}, false);

forge['_get'] = internal.priv.get;
forge['_receive'] = function () {
    var args = arguments;
    // causing horrible latency with newer versions of iOS
    //setZeroTimeout(function () {
        internal.priv.receive.apply(this, args);
    //});
    return "success";
};
