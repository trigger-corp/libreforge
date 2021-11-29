/* global internal, forge */
/*
 * Platform independent API.
 */

// internal helpers for promisifying module methods
internal.promisify = function (f) {
    return function () {
        var args = Array.prototype.slice.call(arguments);
        var promise = new Promise(function(resolve, reject) {
            args.push(resolve);
            args.push(reject);
            f.apply(this, args);
        });
        return promise;
    };
};

internal.promisify_module = function (forge, module) {
    function error(e) {
        internal.priv.call("logging.log", {
            message: "Error promisifying module '" + module + "' " + JSON.stringify(e),
            level: 40
        });
    }

    var api = forge[module];
    var ret = {};

    // copy API
    try {
        ret = Object.keys(api).reduce(function (ret, method) {
            ret[method] = api[method];
            return ret;
        }, ret);
    } catch (e) {
        error(e);
    }

    // promisify API
    try {
        var exclusions = [];
        if ("_syncmethods" in api) {
            exclusions = api._syncmethods;
        }
        ret = Object.keys(api).filter(function (method) {
            return exclusions.indexOf(method) === -1;
        }).filter(function (method) {
            return api.hasOwnProperty(method);
        }).filter(function (method) {
            return method[0] !== "_"; // skip private
        }).filter(function (method) {
            return typeof api[method] === "function";
        }).reduce(function (ret, method) {
            ret[method] = internal.promisify(api[method]);
            return ret;
        }, ret);
    } catch (e) {
        error(e);
    }

    return ret;
};


// Event listeners
internal.listeners = {};
// Temporary storage for events waiting for a listener
internal.eventQueue = {};
internal.queueEvents = true;

// Store callbacks in this
var temporaryAsyncStorage = {};

// All of this is to queue commands if waiting for Catalyst
var callQueue = [];
var callQueueTimeout = null;
var handlingQueue = false;
var handleCallQueue = function () {
    if (callQueue.length > 0) {
        if (!internal.debug || window.catalystConnected) {
            handlingQueue = true;
            while (callQueue.length > 0) {
                var call = callQueue.shift();
                if (call[0] == "logging.log") {
                    console.log(call[1].message);
                }
                internal.priv.call.apply(internal.priv, call);
            }
            handlingQueue = false;
        } else {
            callQueueTimeout = setTimeout(handleCallQueue, 500);
        }
    }
};

// Internal methods to handle communication between privileged and non-privileged code
internal.priv = {
    /**
     * Generic wrapper for native API calls.
     *
     * @param {string} method Name of the API method.
     * @param {*} params Key-values to pass to privileged code.
     * @param {function(...[*])} success Called if native method is successful.
     * @param {function({message: string}=} error
     */
    call: function (method, params, success, error) {
        if ((!internal.debug || window.catalystConnected || method === "internal.showDebugWarning") && (callQueue.length === 0 || handlingQueue)) {
            var callid = forge.tools.UUID();
            var onetime = true;
            // API Methods which can be calledback multiple times
            if (method === "button.onClicked.addListener" || method === "message.toFocussed") {
                onetime = false;
            }
            if (success || error) {
                temporaryAsyncStorage[callid] = {
                    success: success,
                    error: error,
                    onetime: onetime
                };
            }
            var call = {
                callid: callid,
                method: method,
                params: params
            };
            internal.priv.send(call);
            if (window._forgeDebug) {
                try {
                    call.start = (new Date().getTime()) / 1000.0;
                    window._forgeDebug.forge.APICall.apiRequest(call);
                } catch (e) {}
            }
        } else {
            callQueue.push(arguments);
            if (!callQueueTimeout) {
                callQueueTimeout = setTimeout(handleCallQueue, 500);
            }
        }
    },

    /**
     * Calls native code from JS
     * @param {*} data Object to send to privileged/native code.
     */
    send: function () {
        // Implemented in platform specific code
        throw new Error("Forge error: missing bridge to privileged code");
    },

    /**
     * Called from native at the end of asynchronous tasks.
     *
     * @param {Object} result Object containing result details
     */
    lastResult: undefined,
    receive: function (result, returnId) {
        if (returnId !== undefined && returnId === internal.priv.lastResult) {
            return "success";
        }
        internal.priv.lastResult = returnId;
        if (result.callid) {
            // Handle a response
            if (typeof temporaryAsyncStorage[result.callid] === undefined) {
                forge.log("Nothing stored for call ID: " + result.callid);
            }

            var callbacks = temporaryAsyncStorage[result.callid];

            if (callbacks && callbacks[result.status]) {
                callbacks[result.status](result.content);
            }
            if (callbacks && callbacks.onetime) {
                // Remove used callbacks
                delete temporaryAsyncStorage[result.callid];
            }
            if (window._forgeDebug) {
                try {
                    result.end = (new Date().getTime()) / 1000.0;
                    window._forgeDebug.forge.APICall.apiResponse(result);
                } catch (e) {}
            }
        } else if (result.event) {
            // Handle an event
            if (internal.listeners[result.event]) {
                internal.listeners[result.event].forEach(function (callback) {
                    if (result.params) {
                        callback(result.params);
                    } else {
                        callback();
                    }
                });
            } else if (internal.queueEvents) {
                if (internal.eventQueue[result.event]) {
                    internal.eventQueue[result.event].push(result.params);
                } else {
                    internal.eventQueue[result.event] = [result.params];
                }
            }
            if (internal.listeners['*']) {
                internal.listeners['*'].forEach(function (callback) {
                    if (result.params) {
                        callback(result.event, result.params);
                    } else {
                        callback(result.event);
                    }
                });
            }
            if (window._forgeDebug) {
                try {
                    result.start = (new Date().getTime()) / 1000.0;
                    window._forgeDebug.forge.APICall.apiEvent(result);
                } catch (e) {}
            }
        }
        return "success";
    }
};

// We queue events for the first 30 seconds to give apps a change to register listeners
setTimeout(function () {
    internal.queueEvents = false;
    internal.eventQueue = {};
}, 30000);

internal.addEventListener = function (event, callback) {
    if (internal.listeners[event]) {
        internal.listeners[event].push(callback);
    } else {
        internal.listeners[event] = [callback];
    }
    if (internal.eventQueue[event]) {
        internal.eventQueue[event].forEach(function (params) {
            callback(params);
        });
        delete internal.eventQueue[event];
    }
};

/**
 * Generate query string
 */
internal.generateQueryString = function (obj) {
    if (!obj) {
        return "";
    }
    if (!(obj instanceof Object)) {
        return new String(obj).toString();
    }

    var params = [];
    var processObj = function (obj, scope) {
        if (obj === null) {
            return;
        } else if (obj instanceof Array) {
            var index = 0;
            for (var x in obj) {
                var key = (scope ? scope : '') + '[' + index + ']';
                index += 1;
                if (!obj.hasOwnProperty(x)) continue;
                processObj(obj[x], key);
            }
        } else if (obj instanceof Object) {
            for (var x in obj) {
                if (!obj.hasOwnProperty(x)) continue;
                var key = x;
                if (scope) {
                    key = scope + '[' + x + ']';
                }
                processObj(obj[x], key);
            }
        } else {
            params.push(encodeURIComponent(scope)+'='+encodeURIComponent(obj));
        }
    };
    processObj(obj);
    return params.join('&').replace('%20', '+');
};

/**
 * Generate multipart form string
 */
internal.generateMultipartString = function (obj, boundary) {
    if (typeof obj === "string") {
        return '';
    }
    var partQuery = '';
    for (var key in obj) {
        if (!obj.hasOwnProperty(key)) continue;
        if (obj[key] === null) continue;
        // TODO: recursive flatten, deal with arrays
        partQuery += '--'+boundary+'\r\n';
        partQuery += 'Content-Disposition: form-data; name="'+key.replace('"', '\\"')+'"\r\n\r\n';
        partQuery += obj[key].toString()+'\r\n'
    }
    return partQuery;
};

/**
 * Generate a URI from an existing url and additional query data
 */
internal.generateURI = function (uri, queryData) {
    var newQuery = '';
    if (uri.indexOf('?') !== -1) {
        newQuery += uri.split('?')[1]+'&';
        uri = uri.split('?')[0];
    }
    newQuery += this.generateQueryString(queryData)+'&';
    // Remove trailing &
    newQuery = newQuery.substring(0,newQuery.length-1);
    return uri+(newQuery ? '?'+newQuery : '');
};

/**
 * Call a callback with an error that a module is disabled
 */
internal.disabledModule = function (cb, module) {
    var message = "The '"+module+"' module is disabled for this app, enable it in your app config and rebuild in order to use this function";
    forge.logging.error(message);
    cb && cb({
        message: message,
        type: "UNAVAILABLE",
        subtype: "DISABLED_MODULE"
    });
};

// Method to enable debug mode
forge.enableDebug = function () {
    internal.debug = true;
    internal.priv.call("internal.showDebugWarning", {}, null, null);
    internal.priv.call("internal.hideDebugWarning", {}, null, null);
};
// Check the old debug method isn't being used
setTimeout(function () {
    if (window.forge && window.forge.debug) {
        alert("Warning!\n\n'forge.debug = true;' is no longer supported\n\nUse 'forge.enableDebug();' instead.")
    }
}, 3000);
