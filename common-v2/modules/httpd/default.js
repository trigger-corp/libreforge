/* global forge */

forge["httpd"] = {
    // Normalize URLs for httpd like:
    //   content://my.app/file___uri=file%3A%2F%2F%2Fdata%2Fuser%2F0%2Fmy.app%2Fcache%2Fdf966685-29f6-4d92-acbf
    normalize: function (url) {
        if (window.location.protocol !== "http:" && window.location.protocol !== "https:") {
            return url;
        } else if (forge.is.ios()) {
            return forge.httpd._normalize_ios(url);
        } else if (forge.is.android()) {
            return forge.httpd._normalize_android(url);
        } else {
            forge.logging.warn("Unknown platform, could not normalize url: " + url);
            return url;
        }
    },


    _normalize_ios: function (url) {
        var a = document.createElement("a");
        a.href = url;
        if (a.protocol === "content:" && a.hostname == "forge-content") {
            var params = forge.httpd._parseQuery(a.search);
            if ("uri" in params && params.uri.startsWith("http")) {
                a.href = params.uri;
                return params.uri;
            }
        }
        return url;
    },


    _normalize_android: function (url) {
        var a = document.createElement("a");
        a.href = url;
        if (a.protocol === "content:") {
            a.protocol = "http:"; // stop host part from being interpreted as pathname
            var path = a.pathname;
            path = path.replace("___", "?");
            a.href = path;
            a.protocol = window.location.protocol;
            a.hostname = window.location.hostname;
            a.port = window.location.port;
            var params = forge.httpd._parseQuery(a.search);
            if ("uri" in params && params.uri.startsWith("http")) {
                a.href = params.uri;
            }
            return a.href;
        }
        return url;
    },


    _parseQuery: function (queryString) {
        var query = {};
        var pairs = (queryString[0] === '?' ? queryString.substr(1) : queryString).split('&');
        for (var i = 0; i < pairs.length; i++) {
            var pair = pairs[i].split('=');
            query[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || '');
        }
        return query;
    },

    _syncmethods: ["normalize"]
};
