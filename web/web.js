// - imports ------------------------------------------------------------------

var express = require('express');
var http = require('http');
var https = require('https');
var logger = require("morgan");
var bodyParser = require("body-parser");
var multer = require("multer");

var Cookie = require('./cookie').Cookie;


// - create express app -------------------------------------------------------

var app = express();
app.use(logger("dev"));
app.use(express.static(__dirname + '/src'));
app.use(bodyParser.json({limit: "100mb"}));
app.use(bodyParser.urlencoded({ extended: true, limit: "100mb" }));
app.use(multer({ dest: "/tmp" }).any());


// - endpoints ----------------------------------------------------------------

// Killswitch for local toolchain
var debug = !!process.env.FORGE_DEBUG;
if (debug) {
    app.post('/_forge/kill/', function (request, response) {
        response.end();
        process.exit(0);
    });
}

// Default page is index.html
app.get('/', function(request, response) {
    response.sendfile(__dirname +'/src/index.html');
});

// Forge static files
app.get('/_forge/:s', function (request, response) {
    response.sendfile(__dirname +'/forge/'+request.params.s);
});

// Ajax request proxy
app.post(/^\/_forge\/proxy\//, function(request, response) {
    // Add an X header?
    // Check referrer?

    if (!request.body.url) {
        response.statusCode = 404;
        response.end();
        return;
    }

    var url = require('url').parse(request.body.url);

    if ((url.protocol != "http:" && url.protocol != "https:") || !url.hostname) {
        response.statusCode = 404;
        response.end();
        return;
    }

    // Unmunge cookies on user->proxy->url
    Object.keys(request.headers).forEach(function (header) {
        if (header.toLowerCase() == 'cookie') {
            var cookies = [];
            request.headers[header].toString().split(';').forEach(function (cookieStr) {
                try {
                    var cookie = new Cookie().parse(cookieStr);
                    var data = JSON.parse(cookie.value);
                    cookie.value = data.value;
                    cookie.path = data.path;
                    cookie.domain = data.domain;
                    // Check to see if this cookie should be sent with this request
                    if (cookie.collidesWith({domain: url.hostname, path: url.pathname})) {
                        delete cookie.path;
                        delete cookie.domain;
                        cookies.push(cookie.toString());
                    }
                } catch (e) {
                    // Ignore non-munged cookies
                }
            });
            request.body.headers['cookie'] = cookies.join("; ");
        }
    });

    if (!request.body.headers['x-forwarded-for']) {
        request.body.headers['x-forwarded-for'] = request.connection.remoteAddress + (request.headers['x-forwarded-for'] ? ', ' + request.headers['x-forwarded-for'] : '');
    }

    if (!request.body.headers['user-agent']) {
        request.body.headers['user-agent'] = request.headers['user-agent'];
    }

    var options = {
        host: url.hostname,
        port: url.port || (url.protocol == "http:" ? 80 : 443),
        path: url.pathname + (url.search || ''),
        method: request.body.type || 'GET',
        headers: request.body.headers || {}
    };

    var handler = (url.protocol == "http:" ? http : https);

    var req = handler.request(options, function(res) {
        response.statusCode = res.statusCode;
        Object.keys(res.headers).forEach(function (header) {
            if (header.toLowerCase() == 'set-cookie') {
                // several set-cookie headers collapsed into one
                // comma-separated header value is not supported. Set-cookie
                // headers must be one header per cookie.
                var cookieStr = res.headers[header].toString(),
                    cookie = new Cookie().parse(cookieStr);
                cookie.value = JSON.stringify({
                    value: cookie.value,
                    domain: cookie.domain || url.hostname,
                    path: cookie.path
                });
                cookie.path = '/_forge/proxy/'+(cookie.domain || url.hostname).split("").reverse().join("").replace(/\./g, "/");
                delete cookie.domain;
                response.setHeader("Set-Cookie", cookie.toString());
            } else {
                response.setHeader(header, res.headers[header]);
            }
        });
        res.setEncoding('utf8');
        res.on('data', function (chunk) {
            response.write(chunk);
        });
        res.on('end', function () {
            response.end();
        });
    });
    if (request.body.type == 'GET') {
        req.end();
    } else {
        req.end(request.body.data);
    }
});


// - start server -------------------------------------------------------------

var port = process.env.PORT || 3000;
app.listen(port, function() {
    console.log("Listening on " + port);
});

process.on('uncaughtException', function (err) {
    // Don't allow uncaught exceptions to take down the server
    console.log(err);
});
