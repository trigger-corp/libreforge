/* global forge */

if (!("flags" in forge)) {
    forge.flags = {};
}


/**
 * Expose our promise-enabled public API and automatically generate promise
 * wrappers for any modules that haven't been manually wrapped yet
 */
forge.flags.promises = function (enable) {
    if (enable !== true || forge.flags._promises === true) {
        return;
    }
    forge.flags._promises = true;

    window["forge"] = (function (forge) {
        return Object.keys(forge).filter(function (api) {
            return api[0] !== "_";
        }).filter(function (api) {
            return [
                "config",
                "enableDebug",
                "event",
                "flags",
                "inspector",
                "internal",
                "is",
                "logging",
                "live",
                "reload",
                "tools"
            ].indexOf(api) === -1;
        }).reduce(function (ret, api) {
            forge.logging.debug("Enabling promises for: " + api);
            ret[api] = forge.internal.promisify_module(forge, api);
            return ret;
        }, forge);
    })(window["forge"]);
};


/**
 * apply app flag configuration
 */
if ("flags" in forge.config) {
    forge.flags.promises(forge.config.flags.promises);
}
