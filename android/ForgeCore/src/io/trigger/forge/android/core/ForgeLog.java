package io.trigger.forge.android.core;

import android.util.Log;

/**
 * Output log entries to logcat / Trigger toolkit
 */
final public class ForgeLog {
    private ForgeLog() {}

    /**
     * Output a debug level log message.
     * @param message Message to output
     */
    public static void d(String message) {
        if (ForgeLogLevel.equals("INFO") || ForgeLogLevel.equals("WARNING") || ForgeLogLevel.equals("ERROR") || ForgeLogLevel.equals("CRITICAL")) {
            return;
        }
        Log.d("Forge", message);
    }

    /**
     * Output an info level log message.
     * @param message Message to output
     */
    public static void i(String message) {
        if (ForgeLogLevel.equals("WARNING") || ForgeLogLevel.equals("ERROR") || ForgeLogLevel.equals("CRITICAL")) {
            return;
        }
        Log.i("Forge", message);
    }

    /**
     * Output a warning level log message.
     * @param message Message to output
     */
    public static void w(String message) {
        if (ForgeLogLevel.equals("ERROR") || ForgeLogLevel.equals("CRITICAL")) {
            return;
        }
        Log.w("Forge", message);
    }

    /**
     * Output an error level log message.
     * @param message Message to output
     */
    public static void e(String message) {
        if (ForgeLogLevel.equals("CRITICAL")) {
            return;
        }
        Log.e("Forge", message);
    }

    /**
     * Output a critical level log message.
     * @param message Message to output
     */
    public static void c(String message) {
        Log.e("Forge", message);
    }

    /**
     * Sets the log level
     * @param level Log level
     */
    public static void setLogLevel(String level) {
        if (level.equals("DEBUG") || level.equals("INFO") || level.equals("WARNING") || level.equals("ERROR") || level.equals("CRITICAL")) {
            ForgeLogLevel = level;
        }
    }

    private static String ForgeLogLevel = "DEBUG";
}
