/* global forge internal, nullObj */

forge['event'] = {
    'menuPressed': {
        addListener: function (callback, error) {
            internal.addEventListener('event.menuPressed', callback);
        }
    },
    'backPressed': {
        addListener: function (callback, error) {
            internal.addEventListener('event.backPressed', function () {
                callback(function () {
                    internal.priv.call('event.backPressed_closeApplication', {});
                }, function () {
                    internal.priv.call('event.backPressed_pauseApplication', {});
                });
            });
        },
        preventDefault: function (success, error) {
            internal.priv.call('event.backPressed_preventDefault', {}, success, error);
        },
        restoreDefault: function (success, error) {
            internal.priv.call('event.backPressed_restoreDefault', {}, success, error);
        }
    },
    'messagePushed': {
        addListener: function (callback, error) {
            internal.addEventListener('event.messagePushed', callback);
        }
    },
    'orientationChange': {
        addListener: function (callback, error) {
            internal.addEventListener('event.orientationChange', callback);

            if (typeof nullObj !== "undefined" && internal.currentOrientation !== nullObj) {
                internal.priv.receive({
                    event: 'event.orientationChange'
                });
            }
        }
    },
    'connectionStateChange': {
        addListener: function (callback, error) {
            internal.addEventListener('event.connectionStateChange', callback);
        }
    },
    'appPaused': {
        addListener: function (callback, error) {
            internal.addEventListener('event.appPaused', callback);
        }
    },
    'appResumed': {
        addListener: function (callback, error) {
            internal.addEventListener('event.appResumed', callback);
        }
    },
    'statusBarTapped': {
        addListener: function (callback, error) {
            internal.addEventListener('event.statusBarTapped', callback);
        }
    },

    'keyboardWillShow': {
        addListener: function (callback, error) {
            internal.addEventListener('event.keyboardWillShow', callback);
        }
    },
    'keyboardWillHide': {
        addListener: function (callback, error) {
            internal.addEventListener('event.keyboardWillHide', callback);
        }
    },
    'keyboardDidShow': {
        addListener: function (callback, error) {
            internal.addEventListener('event.keyboardDidShow', callback);
        }
    },
    'keyboardDidHide': {
        addListener: function (callback, error) {
            internal.addEventListener('event.keyboardDidHide', callback);
        }
    }
};
