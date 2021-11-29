/* global forge internal */

forge["layout"] = {
    "getSafeAreaInsets": function(success, error) {
        internal.priv.call("layout.getSafeAreaInsets", {}, success, error);
    }
};
