/* globals module, require */

module.exports = function(grunt) {
    require("matchdep").filterDev("grunt-*").forEach(grunt.loadNpmTasks);

    grunt.log.writeln("Options: " + JSON.stringify(grunt.option.flags()));
    grunt.log.writeln("Target: " + grunt.option("target"));
    if (!grunt.option("target")) {
        grunt.log.writeln("Error: no target specified");
        return false;
    }
    grunt.log.writeln("Port: " + grunt.option("port"));
    if (!grunt.option("port")) {
        grunt.log.writeln("Error: no port specified");
        return false;
    }

    grunt.initConfig({
        express: {
            all: {
                options: {
                    port: grunt.option("port"),
                    hostname: "0.0.0.0",
                    bases: ["../../<%= forge." + grunt.option("target") + ".dest%>"],
                    livereload: true
                }
            }
        },

        watch: {
            src: {
                options: {
                    event: ["changed"], // TODO add
                    livereload: true,
                    livereloadOnError: false, // don't trigger reload if any tasks fail
                    spawn: false,             // faster but more likely to fail
                    cwd: "../.."
                },
                files: [ "src/**" ],
                tasks: [ "copy:sources", "copy:platform", "forge:update:<%= grunt.option('target')%>" ]
            }
        },

        copy: {
            sources: {
                files: [ {
                    expand:true,
                    cwd: "../../src/",
                    src: ["**"],
                    dest: "../../<%= forge." + grunt.option("target") + ".dest%>/src/"
                } ]
            },
            platform: {
                src: "../../src/index.html",
                dest: "../../<%= forge." + grunt.option("target") + ".dest%>/src/index.html",
                options: {
                    process: function (content, srcpath) {
                        return content.replace(/<head>/i,
                                               grunt.template.process("<head><%= forge."  +
                                                                      grunt.option("target") +
                                                                      ".include%>"));
                    }
                }
            }
        },

        forge: {
            ios: {
                dest: "development/ios/simulator-ios.app/assets",
                include: "<script src='../forge/app_config.js'></script><script src='../forge/all.js'></script>"
            },
            android: {
                dest: "development/android/assets",
                include: "<script src='../forge/app_config.js'></script><script src='../forge/all.js'></script>"
            },
            web: {
                dest: "development/web",
                include: "<script src='../_forge/app_config.js'></script><script src='../_forge/all.js'></script>"
            }
        }
    });

    grunt.registerTask("forge", "do a forge build", function() {
        var base = grunt.template.process("http://localhost:<%= express.all.options.bases%>/src/index.html");
        var dest = grunt.template.process("../../<%= forge." + grunt.option("target") + ".dest%>/src/");
        return true;
    });

    grunt.registerTask("serve", [
        "express",
        "watch"
    ]);
};
