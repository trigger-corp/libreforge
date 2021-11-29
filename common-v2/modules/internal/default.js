/* global forge, internal */
forge['internal'] = {
    'ping': function (data, success, error) {
        internal.priv.call("internal.ping", {data: [data]}, success, error);
    },
    'call': internal.priv.call,
    'addEventListener': internal.addEventListener,
    listeners: internal.listeners,
    'configForModule': function (namespace) {
        return forge.config.modules[forge.module_mapping[namespace]].config;
    },
    'promisify_module': internal.promisify_module
};
