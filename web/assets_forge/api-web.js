/*
 * api-web.js
 *
 * Web specific overrides to the generic Forge api.js
 */

// Don't error for non-existant backend
internal.priv.send = function () {};

forge.is.web = function () {
    return true;
}

forge.notification.create = function(title, text, success, error) {
    Notification.requestPermission(function (permission) {
        if (permission !== "granted") {
            error && error({
                message: "User did not grant permission to display notifications"
            });
            return;
        }
        var notification = new Notification(title, { body: text });
        success && success();
    });
}

forge.tools.getURL = function(name, successCallback, errorCallback) {
    name = name.toString();
    if (name.indexOf("http://") === 0 || name.indexOf("https://") === 0) {
        successCallback(name);
    } else {
        successCallback(window.location.protocol + '//' + window.location.host + ((name.indexOf("/") === 0) ? name : ("/" + name) ));
    }
}

forge.request.ajax = function(options) {
    var url = (options.url ? options.url : null);
    var success = (options.success ? options.success : undefined);
    var error = (options.error ? options.error : undefined);
    var username = (options.username ? options.username : null);
    var password = (options.password ? options.password : null);
    var accepts = (options.accepts ? options.accepts : ["*/*"]);
    var cache = (options.cache ? options.cache : false);
    var contentType = (options.contentType ? options.contentType : null);
    var data = (options.data ? options.data : null);
    var dataType = (options.dataType ? options.dataType : null);
    var headers = (options.headers ? options.headers : {});
    // TODO: Switch to milliseconds on mobile
    var timeout = (options.timeout ? options.timeout : 60000);
    var type = (options.type ? options.type : 'GET');

    if (typeof accepts === "string") {
        // Given "text/html" instead of ["text/html"].
        accepts = [accepts];
    }
    if (type == 'GET') {
        url = internal.generateURI(url, data);
        data = null;
    } else if (data) {
        data = internal.generateQueryString(data);
        if (!contentType) {
            contentType = "application/x-www-form-urlencoded";
        }
        headers['Content-Length'] = data.length;
    }

    if (cache) {
        cache = {};
        cache['wm'+Math.random()] = Math.random();
        url = internal.generateURI(url, cache);
    }
    if (accepts) {
        headers['Accept'] = accepts.join(',');
    }
    if (contentType) {
        headers['Content-Type'] = contentType;
    }
    // TODO: Authentication headers

    var passBack = {
        url: url,
        data: data,
        headers: headers,
        type: type
    }

    $.ajax({
        url: '/_forge/proxy/'+url.match(/\/\/([^\/:]+)/)[1].split("").reverse().join("").replace(/\./g, "/")+'/',
        type: 'POST',
        data: passBack,
        dataType: 'text',
        timeout: timeout,
        success: success && function (data) {
            try {
                if (dataType == 'xml') {
                    // Borrowed from jQuery.
                    var tmp, xml;
                    if ( window.DOMParser ) { // Standard
                        tmp = new DOMParser();
                        xml = tmp.parseFromString(data , "text/xml");
                    } else { // IE
                        xml = new ActiveXObject( "Microsoft.XMLDOM" );
                        xml.async = "false";
                        xml.loadXML(data);
                    }

                    data = xml;
                } else if (dataType == 'json') {
                    data = JSON.parse(data);
                }
            } catch (e) {
            }
            success(data);
        },
        error: function (xhr, status, err) {
            error({
                message: 'api.ajax with ' + JSON.stringify(options) + 'failed. ' + status + ': ' + err,
                type: 'EXPECTED_FAILURE',
                status: status,
                statusCode: xhr.status,
                err: err
            });
        }
    });
}

forge.prefs = {
    get: function (key, success, error) {
        try {
            var value = localStorage[key];
            if (value === "undefined") {
                success && success(undefined);
            } else if (value === null || value === undefined) {
                success && success(null);
            } else {
                success && success(JSON.parse(value));
            }
        } catch (e) {
            error && error();
        }
    },
    set: function (key, value, success, error) {
        try {
            if (value === undefined) {
                localStorage[key] = "undefined";
            } else {
                localStorage[key] = JSON.stringify(value);
            }
            success && success();
        } catch (e) {
            error && error();
        }
    },
    keys: function(success, error) {
        success && success(Object.keys(localStorage));
    },
    all: function(success, error) {
        try {
            var prefs = {};
            Object.keys(localStorage).forEach(function (key) {
                prefs[key] = JSON.parse(localStorage[key]);
            })
            sucess && success(prefs);
        } catch (e) {
            error && error();
        }
    },
    clear: function(key, success, error) {
        localStorage.removeItem(key);
        success && success();
    },
    clearAll: function(success, error) {
        localStorage.clear();
        success && success();
    }
};

forge.tabs = {
    open: function (url, success, error) {
        window.open(url, "_blank");
        success();
    }
};
