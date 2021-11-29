forge['live'] = {
    'restartApp': function(success, error) {
        internal.priv.call("live.restartApp", {}, success, error);
    },
    'restartServer': function(success, error) {
        internal.priv.call("live.restartServer", {}, success, error);
    },
    'reloadInitialPage': function(success, error) {
        internal.priv.call("live.reloadInitialPage", {}, success, error);
    }
};

var fireOnce = true;
var RegisterForgeLivePlugin = function() {
    document.removeEventListener("DOMContentLoaded", RegisterForgeLivePlugin, false);
    if (typeof window.LiveReload !== "undefined" && forge.is.mobile()) {
        var ForgeLivePlugin = (function() {
            function ForgeLivePlugin(window, host) {
                this.window = window;
                this.host = host;
            }
            ForgeLivePlugin.prototype.reload = function(path, options) {
                if (path.match(/\.css$/i)) {
                    return false;
                } else if (path.match(/\.(jpe?g|png|gif)$/i)) {
                    return false;
                }
                if (fireOnce) {
                    fireOnce = false;
                    forge.live.restartApp();
                }
                return true;
            };
            ForgeLivePlugin.identifier = "forgelive";
            ForgeLivePlugin.version = "1.0";
            return ForgeLivePlugin;
        })();
        window.LiveReload.addPlugin(ForgeLivePlugin);
    }
};
document.addEventListener("DOMContentLoaded", RegisterForgeLivePlugin, false);
