forge['is']['mobile'] = function() {
    return true;
};

forge['is']['android'] = function() {
    return true;
};

forge['is']['orientation']['portrait'] = function () {
    return internal.currentOrientation == 'portrait';
};

forge['is']['orientation']['landscape'] = function () {
    return internal.currentOrientation == 'landscape';
};

forge['is']['connection']['connected'] = function () {
    return internal.currentConnectionState.connected;
};

forge['is']['connection']['wifi'] = function () {
    return internal.currentConnectionState.wifi;
};
