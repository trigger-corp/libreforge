/*global forge, $*/
/*exported runOnce, askQuestion, runAutomatedTests, runInteractiveTests*/
var getModules = function () {
    var modules = [];
    for (var x in forge.config.modules) {
        modules.push(x);
    }
    return modules;
};
var runAutomatedTests = function () {
    delete window.QUnit;
    $('body').append('<script src="js/qunit-1.10.0.js"></sc'+'ript>');
    $('body').append('<script>QUnit.config.reorder = false;QUnit.config.autostart = false;QUnit.config.autorun = false;</sc'+'ript>');
    $.each(getModules(), function (i, module) {
        $('body').append('<script src="../forge/tests/automated/'+module+'.js"></sc'+'ript>');
    });
    $('body').append('<script>QUnit.load(); setTimeout(function () {QUnit.start()}, 100);</sc'+'ript>');
};
var runInteractiveTests = function () {
    delete window.QUnit;
    $('body').append('<script src="js/qunit-1.10.0.js"></sc'+'ript>');
    $('body').append('<script>QUnit.config.reorder = false;QUnit.config.autostart = false;QUnit.config.autorun = false;</sc'+'ript>');
    $.each(getModules(), function (i, module) {
        $('body').append('<script src="../forge/tests/interactive/'+module+'.js"></sc'+'ript>');
    });
    $('body').append('<script>QUnit.load(); setTimeout(function () {QUnit.start()}, 100);</sc'+'ript>');
};

var askQuestion = function (question, buttons) {
    $('#qunit-interact').html('');
    var div = $('<div class="alert alert-info alert-block">').append($('<p style="font-size: 1.2em">').html(question));
    var btnGroup = $('<div>');
    var addButton = function (button, cb) {
        btnGroup.append($('<button style="margin: 5px;" class="btn btn-primary">').text(button).click(function () {
            $('#qunit-interact').html('');
            cb && cb();
        }));
    };
    for (var button in buttons) {
        addButton(button, buttons[button]);
    }
    div.append(btnGroup);
    $('#qunit-interact').append(div);
};

var runOnce = function (func) {
    var run = true;
    return function () {
        if (run) {
            func();
        }
        run = false;
    };
};

// helper for logging consistent and informative api errors
var apiError = function (api) {
    return function (e) {
        ok(false, api + " failure: " + e.message);
        start();
    };
};
