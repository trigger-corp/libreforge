/* global forge, internal */

forge["tools"] = {
    /**
     * Creates an RFC 4122 compliant UUID.
     *
     * http://www.rfc-archive.org/getrfc.php?rfc=4122
     *
     * @return {string} A new UUID.
     */
    "UUID": function() {
        // Implemented in JS on all platforms. No point going to native for this.
        return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0;
            var v = c == "x" ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        }).toUpperCase();
    },


    /**
     * Resolve this name to a fully-qualified local or remote resource.
     * The resource is not checked for existence.
     * This method does not load the resource. For that, use "getPage()".
     *
     * For example, unqualified name: "my/resource.html"
     * On iOS: "https://localhost:31337/src/my/resource.html"
     * On Android: "content://io.trigger.android.forge.inspector/src/resource.html"
     *
     * @param {string} resource Unqualified resource.
     * @param {function(string)=} success Response data
     * @param {function({message: string}=} error
     */
    "getURL": function(resource, success, error) {  // deprecated
        if (resource.uri) {
            success(resource.uri);
            return;
        }
        internal.priv.call("tools.getURLFromSourceDirectory", {
            resource: resource.toString()
        }, success, error);
    },
    "getURLFromSourceDirectory": function(resource, success, error) {
        internal.priv.call("tools.getURLFromSourceDirectory", {
            resource: resource.toString()
        }, success, error);
    },

    /**
     * Get file object for a local file.
     *
     * @param {string} resource
     * @param {function(file: File)=} success
     * @param {function({message: string}=} error
     */
    "getLocal": function (resource, success, error) {  // deprecated
        internal.priv.call("tools.getFileFromSourceDirectory", {
            resource: resource
        }, success, error);
    },
    "getFileFromSourceDirectory": function (resource, success, error) {
        internal.priv.call("tools.getFileFromSourceDirectory", {
            resource: resource
        }, success, error);
    },


    /**
     * Gets all cookies
     */
    "getCookies": function (success, error) {
        if (forge.is.ios()) {
            internal.priv.call("tools.getCookies", {}, success, error);
        } else {
            forge.logging.log("forge.tools.getCookies() is only supported on iOS");
            success([]);
        }
    },

    /**
     * Sets a cookie
     */
    "setCookie": function (domain, path, name, value, success, error) {
        if (forge.is.ios()) {
            internal.priv.call("tools.setCookie", {
                domain: domain,
                path: path,
                name: name,
                value: value
            }, success, error);
        } else {
            forge.logging.log("forge.tools.setCookie() is only supported on iOS");
            success();
        }
    },

    /**
     * Opens an url in the app's webview.
     *
     * @param {string} url
     */
    "openInWebView": function (url, success, error) {
        internal.priv.call("tools.openInWebView", {
            url: url.toString()
        }, success, error);
    },

    /**
     * Opens an url with the device's default handler for the given content type.
     *
     * @param {string} url
     */
    "openWithDevice": function (url, success, error) {
        internal.priv.call("tools.openWithDevice", {
            url: url.toString()
        }, success, error);
    }
};
