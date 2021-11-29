/*global forge, $*/
/*exported runOnce, askQuestion*/

forge.inspector = {
    getFixture: function (module, file) {
        var location = window.location.href;
        var url = decodeURI(location.substring(0, location.length-(10 + window.location.search.length + window.location.hash.length)));
        url = url + 'fixtures/' + module + (file.substring(0, 1) == '/' ? '' : '/') + file;
        return {
            uri: url
        };
    }
};

var getModules = function () {
    var modules = [];
    for (var x in forge.config.modules) {
        modules.push(x);
    }
    return modules;
};

var runTests = function () {
    $('body').append('<script src="js/qunit-1.10.0.js"></sc'+'ript>');
    $('body').append('<script>QUnit.config.reorder = false;QUnit.config.autostart = false;QUnit.config.autorun = false;</sc'+'ript>');
    $.each(getModules(), function (i, module) {
        $('body').append('<script src="tests/'+module+'.js"></sc'+'ript>');
    });
    $('body').append('<script src="js/qunit_hooks.js"></sc'+'ript>');
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

var askQuestion = function (question, buttons) {
    // Backwards compatible with yes/no style call
    if (arguments.length == 3) {
        buttons = {
            Yes: arguments[1],
            No: arguments[2]
        };
    }
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

$(function () {
    runTests();
});
