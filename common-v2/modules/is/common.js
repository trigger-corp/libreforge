/* global forge */
forge['is'] = {
    /**
     * @return {boolean}
     */
    'mobile': function() {
        return false;
    },
    /**
     * @return {boolean}
     */
    'desktop': function() {
        return false;
    },
    /**
     * @return {boolean}
     */
    'android': function() {
        return false;
    },
    /**
     * @return {boolean}
     */
    'ios': function() {
        return false;
    },
    /**
     * @return {boolean}
     */
    'web': function() {
        return false;
    },
    /**
     * @return {boolean}
     */
    'development': function() {
        if ("config" in forge && "development" in forge.config) {
            return forge.config.development;
        } else {
            return false;
        }
    },
    'orientation': {
        'portrait': function () {
            return false;
        },
        'landscape': function () {
            return false;
        }
    },
    'connection': {
        'connected': function () {
            return true;
        },
        'wifi': function () {
            return true;
        }
    }
};
