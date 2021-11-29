package io.trigger.forge.android.core;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.lang.annotation.Annotation;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Vector;
import java.util.WeakHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

import android.app.Application;
import android.content.Intent;
import android.os.Build;
import android.os.Handler;
import android.util.Pair;
import android.webkit.ValueCallback;

import com.google.common.base.Throwables;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParseException;
import com.google.gson.JsonParser;
import com.google.gson.JsonPrimitive;
import com.google.gson.stream.JsonReader;
import com.llamalab.safs.FileSystems;
import com.llamalab.safs.android.AndroidFileSystem;
import com.llamalab.safs.android.AndroidFileSystemProvider;

/**
 * Static access to various useful parts of the application, as well as methods to control communication between Javascript and Java.
 */
public class ForgeApp extends Application {
    static {
        // initialize java.nio.file backport
        System.setProperty("com.llamalab.safs.spi.DefaultFileSystemProvider", AndroidFileSystemProvider.class.getName());
    }

    private static ForgeActivity activity;
    private static ForgeApp app;
    private static Map<String, Method> cachedMethods = new HashMap<String, Method>();
    private static Vector<ForgeEventListener> eventListeners = new Vector<ForgeEventListener>();

    private static WeakHashMap<ForgeWebView, Boolean> reflectionReady = new WeakHashMap<ForgeWebView, Boolean>();
    private static WeakHashMap<ForgeWebView, Handler> handler = new WeakHashMap<ForgeWebView, Handler>();
    private static WeakHashMap<ForgeWebView, Method> callJS = new WeakHashMap<ForgeWebView, Method>();
    private static WeakHashMap<ForgeWebView, Object> browserFrame = new WeakHashMap<ForgeWebView, Object>();

    private static JsonParser parser = new JsonParser();
    private static Vector<Pair<ForgeWebView, JsonObject>> javascriptReturnQueue = new Vector<Pair<ForgeWebView,JsonObject>>();
    private static boolean returning = false;
    public static JsonObject appConfig;
    public static JsonObject moduleMapping;

    /**
     * @hide
     */
    public static boolean inspectorEnabled = false;

    /**
     * @hide
     */
    public ForgeApp() {
    }

    @Override
    public void onCreate() {
        // initialize java.nio.file backport
        ((AndroidFileSystem)FileSystems.getDefault()).setContext(this);

        app = this;
        try {
            InputStream is = getAssets().open("app_config.json");
            JsonReader reader = new JsonReader(new InputStreamReader(is, "UTF-8"));
            JsonElement configElement = new JsonParser().parse(reader);
            appConfig = configElement.getAsJsonObject();

            is = getAssets().open("module_mapping.json");
            reader = new JsonReader(new InputStreamReader(is, "UTF-8"));
            configElement = new JsonParser().parse(reader);
            moduleMapping = configElement.getAsJsonObject();
        } catch (IOException e) {
            ForgeLog.c("Error reading app_config.json");
            throw new RuntimeException("Error reading app_config.json");
        } catch (JsonParseException e) {
            ForgeLog.c("Error parsing app_config.json");
            throw new RuntimeException("Error parsing app_config.json");
        }

        if (appConfig.has("core")
                && appConfig.getAsJsonObject("core").has("general")
                && appConfig.getAsJsonObject("core").getAsJsonObject("general").has("logging")
                && appConfig.getAsJsonObject("core").getAsJsonObject("general").getAsJsonObject("logging").has("level")) {
            String level = appConfig.getAsJsonObject("core").getAsJsonObject("general").getAsJsonObject("logging").get("level").getAsString();
            ForgeLog.setLogLevel(level);
        }

        HashSet<String> enabledModules = new HashSet<String>();
        enabledModules.add("internal");
        enabledModules.add("logging");
        enabledModules.add("event");
        if (ForgeApp.flag("android_disable_httpd") != true) {
            enabledModules.add("httpd");
        }
        enabledModules.add("tools");
        enabledModules.add("reload");
        enabledModules.add("live");
        enabledModules.add("layout");

        for (Entry<String, JsonElement> module : moduleMapping.entrySet()) {
            enabledModules.add(module.getKey());
        }

        ForgeApp.clearEventListeners();
        ForgeApp.clearAPIMethods();
        for (String module : enabledModules) {
            // Event listeners
            String className = "io.trigger.forge.android.modules." + module + ".EventListener";
            try {
                Class eventListener = Class.forName(className);
                Constructor<ForgeEventListener> eventListenerConstructor = eventListener.getConstructor();
                ForgeEventListener eventListenerInstance = eventListenerConstructor.newInstance();
                ForgeApp.addEventListener(eventListenerInstance);
            } catch (ClassNotFoundException e) {
            } catch (NoSuchMethodException e) {
            } catch (IllegalArgumentException e) {
            } catch (InstantiationException e) {
            } catch (IllegalAccessException e) {
            } catch (InvocationTargetException e) {
            }

            // API Methods
            className = "io.trigger.forge.android.modules." + module + ".API";
            String jsModule = module;
            try {
                Class moduleAPI = Class.forName(className);
                for (Method apiMethod : moduleAPI.getDeclaredMethods()) {
                    if (Modifier.isPublic(apiMethod.getModifiers())) {
                        ForgeApp.addAPIMethod(jsModule + "." + apiMethod.getName(), apiMethod);
                    }
                }
            } catch (ClassNotFoundException e) {
            }

            if (module.equals("inspector")) {
                ForgeApp.inspectorEnabled = true;
            }
        }
        super.onCreate();

        ForgeApp.nativeEvent("onApplicationCreate", new Object[] { });
    }

    /**
     * Register an API method to be used with Javascript calls.
     * @hide
     */
    public static void addAPIMethod(final String methodName, final Method method) {
        cachedMethods.put(methodName, method);
    }

    /**
     * @hide
     */
    public static void addEventListener(ForgeEventListener eventListener) {
        ForgeApp.eventListeners.add(eventListener);
    }

    /**
     * Get the current activity. Useful for many Android methods which require a context.
     * @return Current activity.
     */
    public static ForgeActivity getActivity() {
        return activity;
    }

    public static ForgeApp getApp() {
        return app;
    }

    /**
     * @hide
     */
    public static void setActivity(ForgeActivity activity) {
        // Reset the return queue when we have a new main activity
        javascriptReturnQueue = new Vector<Pair<ForgeWebView,JsonObject>>();
        ForgeApp.activity = activity;
    }

    /**
     * Get the default FileProvider authority. Useful for FileProvider methods which require an authority.
     * @return FileProvider authority.
     */
    public static String getFileProviderAuthority() {
        return ForgeApp.getActivity().getApplicationContext().getPackageName() + ".ForgeFileProvider";
    }

    /**
     * @hide
     */
    public static void clearAPIMethods() {
        cachedMethods.clear();
    }

    /**
     * @hide
     */
    public static void clearEventListeners() {
        ForgeApp.eventListeners = new Vector<ForgeEventListener>();
    }

    /**
     * Method accessed from Javascript, allows a Java method to be invoked by the Javascript API.
     * @hide
     */
    public static void callJavaFromJavaScript(final ForgeWebView webView, final String callid, final String method, final String params) {
        if (callid.equals("ready")) {
            // First call sent back so we know when Javascript is ready
            triggerReturn();
            return;
        }

        if (!method.equals("logging.log")) {
            ForgeLog.d("Native call " + method + " with task.params: " + (params == null ? "(null)" : (params.length() == 0 ? "(empty)" : params.toString())));
        }

        final Method foundMethod = cachedMethods.get(method);

        ForgeTask task;
        JsonObject jsonParams = null;
        try {
            jsonParams = (JsonObject) parser.parse(params);
        } catch (ClassCastException e) {
            ForgeLog.e("Failed to parse JSON set to Java from JavaScript: "+params);
        } catch (JsonParseException e) {
            ForgeLog.e("Failed to parse JSON set to Java from JavaScript: "+params);
        }

        task = new ForgeTask(callid, jsonParams, webView);

        if (foundMethod == null) {
            task.error("Method not supported on this platform: " + method, "UNAVAILABLE", null);
        } else {
            // Build up parameters to pass to method
            Annotation[][] parameterAnnotations = foundMethod.getParameterAnnotations();
            Object[] parameter = new Object[parameterAnnotations.length];
            // Always pass the task in as the first parameter
            parameter[0] = task;

            Class<?>[] parameterTypes = foundMethod.getParameterTypes();

            // Loop through the rest of the parameters
            for (int i = 1; i < parameterAnnotations.length; i++) {
                boolean paramFound = false;
                Annotation[] annotations = parameterAnnotations[i];
                for(Annotation annotation : annotations) {
                    if (annotation instanceof ForgeParam) {
                        String paramKey = ((ForgeParam) annotation).value();
                        if (!jsonParams.has(paramKey)) {
                            // Missing key from JS
                            task.error("Missing required parameter: "+paramKey, "UNEXPECTED_FAILURE", null);
                            return;
                        }

                        Class<?> paramType = parameterTypes[i];
                        if (paramType == String.class) {
                            JsonPrimitive primitive = jsonParams.getAsJsonPrimitive(paramKey);
                            if (primitive != null && primitive.isString()) {
                                parameter[i] = primitive.getAsString();
                                paramFound = true;
                            } else {
                                task.error("Parameter '"+paramKey+"' was of the wrong type, expected a string", "UNEXPECTED_FAILURE", null);
                                return;
                            }
                        } else if (paramType == boolean.class) {
                            JsonPrimitive primitive = jsonParams.getAsJsonPrimitive(paramKey);
                            if (primitive != null && primitive.isBoolean()) {
                                parameter[i] = primitive.getAsBoolean();
                                paramFound = true;
                            } else {
                                task.error("Parameter '"+paramKey+"' was of the wrong type, expected a boolean", "UNEXPECTED_FAILURE", null);
                                return;
                            }
                        } else if (paramType == int.class) {
                            JsonPrimitive primitive = jsonParams.getAsJsonPrimitive(paramKey);
                            if (primitive != null && primitive.isNumber()) {
                                parameter[i] = primitive.getAsInt();
                                paramFound = true;
                            } else {
                                task.error("Parameter '"+paramKey+"' was of the wrong type, expected an int", "UNEXPECTED_FAILURE", null);
                                return;
                            }
                        } else if (paramType == long.class) {
                            JsonPrimitive primitive = jsonParams.getAsJsonPrimitive(paramKey);
                            if (primitive != null && primitive.isNumber()) {
                                parameter[i] = primitive.getAsLong();
                                paramFound = true;
                            } else {
                                task.error("Parameter '"+paramKey+"' was of the wrong type, expected a long", "UNEXPECTED_FAILURE", null);
                                return;
                            }
                        } else if (paramType == double.class) {
                            JsonPrimitive primitive = jsonParams.getAsJsonPrimitive(paramKey);
                            if (primitive != null && primitive.isNumber()) {
                                parameter[i] = primitive.getAsDouble();
                                paramFound = true;
                            } else {
                                task.error("Parameter '"+paramKey+"' was of the wrong type, expected a double", "UNEXPECTED_FAILURE", null);
                                return;
                            }
                        } else if (paramType == JsonObject.class) {
                            JsonElement element = jsonParams.get(paramKey);
                            if (element != null && element.isJsonObject()) {
                                parameter[i] = element.getAsJsonObject();
                                paramFound = true;
                            } else {
                                task.error("Parameter '"+paramKey+"' was of the wrong type, expected an object", "UNEXPECTED_FAILURE", null);
                                return;
                            }
                        } else if (paramType == JsonArray.class) {
                            JsonElement element = jsonParams.get(paramKey);
                            if (element != null && element.isJsonArray()) {
                                parameter[i] = element.getAsJsonArray();
                                paramFound = true;
                            } else {
                                task.error("Parameter '"+paramKey+"' was of the wrong type, expected an array", "UNEXPECTED_FAILURE", null);
                                return;
                            }
                        } else {
                            task.error("Parameter '"+paramKey+"' is an invalid type: "+paramType.toString(), "UNEXPECTED_FAILURE", null);
                            return;
                        }
                    }
                }
                if (!paramFound) {
                    task.error("API method is missing annotations on parameters.", "UNEXPECTED_FAILURE", null);
                    return;
                }
            }
            try {
                foundMethod.invoke(null, parameter);
            } catch (InvocationTargetException ex) {
                ForgeLog.w("Error while executing API method: " + method);
                task.error(Throwables.getRootCause(ex));
            } catch (Exception ex) {
                ForgeLog.w("Error while executing API method: " + method);
                task.error(ex);
            }
        }
    }

    /**
     * Trigger an event in forge within Javascript. For example, menu button pressed
     * @param name The event name i.e. 'events.menuPressed'
     * @param params Any additional data to pass back with the event.
     */
    public static void event(final String name, final JsonElement params) {
        if (ForgeApp.getActivity() != null && ForgeApp.getActivity().webView != null) {
            JsonObject result = new JsonObject();
            result.addProperty("event", name);
            result.add("params", params);

            returnObject(ForgeApp.getActivity().webView, result);
        } else {
            ForgeLog.w("Failed to return to JS, WebView is probably not ready.");
        }
    }

    /**
     * Trigger an event in forge within Javascript. For example, menu button pressed
     * @param name The event name i.e. 'events.menuPressed'
     */
    public static void event(final String name) {
        event(name, null);
    }

    /**
     * Return a JsonObject containing details about all loaded API methods.
     * Used for inspecting modules.
     * @return
     */
    public static JsonObject getAPIMethodInfo() {
        JsonObject result = new JsonObject();

        for (Map.Entry<String, Method> method : cachedMethods.entrySet()) {
            String apiMethod = method.getKey();
            Method javaMethod = method.getValue();
            JsonObject details = new JsonObject();

            Annotation[][] parameterAnnotations = javaMethod.getParameterAnnotations();
            Class<?>[] parameterTypes = javaMethod.getParameterTypes();

            for (int i = 1; i < parameterAnnotations.length; i++) {
                Annotation[] annotations = parameterAnnotations[i];
                for (Annotation annotation : annotations) {
                    if (annotation instanceof ForgeParam) {
                        Class<?> paramType = parameterTypes[i];
                        JsonObject paramDetails = new JsonObject();
                        paramDetails.addProperty("type", paramType.getName());
                        details.add(((ForgeParam) annotation).value(), paramDetails);
                    }
                }
            }
            result.add(apiMethod, details);
        }

        return result;
    }

    /**
     * @hide
     */
    private static boolean isLoggableEvent(String event) {
        if (event.equals("onUserInteraction")) {
            return false;
        }
        if (event.equals("onTouchEvent")) {
            return false;
        }
        if (event.equals("onWindowFocusChanged")) {
            return false;
        }
        return true;
    }

    /**
     * @hide
     */
    public static Object nativeEvent(final String method, Object[] args) {
        if (inspectorEnabled && isLoggableEvent(method)) {
            JsonObject result = new JsonObject();
            result.addProperty("name", method);
            event("inspector.eventTriggered", result);
        }

        Object returnValue = null;
        outerloop:
            for (final ForgeEventListener eventListener : eventListeners) {
                for (Method moduleMethod : eventListener.getClass().getDeclaredMethods()) {
                    // TODO: Cache methods?
                    if (moduleMethod.getName().equals(method)) {
                        try {
                            if (inspectorEnabled && isLoggableEvent(method)) {
                                JsonObject result = new JsonObject();
                                result.addProperty("name", method);
                                result.addProperty("class", eventListener.getClass().getName());
                                event("inspector.eventInvoked", result);
                            }
                            returnValue = moduleMethod.invoke(eventListener, args);
                            if (returnValue != null) {
                                break outerloop;
                            }
                        } catch (IllegalArgumentException e) {
                        } catch (IllegalAccessException e) {
                        } catch (InvocationTargetException e) {
                        }
                    }
                }
            }
        // If we don't have a return value get the default
        if (returnValue == null) {
            for (Method moduleMethod : ForgeEventListener.class.getDeclaredMethods()) {
                if (moduleMethod.getName().equals(method)) {
                    try {
                        // TODO: cache instance?
                        returnValue = moduleMethod.invoke(new ForgeEventListener() {}, args);
                    } catch (IllegalArgumentException e) {
                    } catch (IllegalAccessException e) {
                    } catch (InvocationTargetException e) {
                    }
                }
            }
        }
        return returnValue;
    }

    /**
     * Invoke an intent and handle response with callback
     *
     * @param intent Intent to be invoked
     * @param handler Callback for Intent results
     */
    public static void intentWithHandler(Intent intent, ForgeIntentResultHandler handler) {
        int requestCode = getActivity().registerIntentHandler(handler);
        getActivity().startActivityForResult(intent, requestCode);
    }

    private static void returnNextObj() {
        if (javascriptReturnQueue.size() == 0) {
            returning = false;
            return;
        }

        final Pair<ForgeWebView, JsonObject> toReturn = javascriptReturnQueue.remove(0);

        boolean b = false;
        if (toReturn.second.has("content")
                && toReturn.second.get("content").isJsonObject()
                && toReturn.second.getAsJsonObject("content").has("method")
                && toReturn.second.getAsJsonObject("content").get("method").isJsonPrimitive()) {
            String method = toReturn.second.getAsJsonObject("content").get("method").getAsString();
            b = method.equals("logging.log");
        }
        final boolean isLoggingNoise = b;

        final String returnStr = toReturn.second.toString();
        final ForgeWebView webView = toReturn.first;
        if (Build.VERSION.SDK_INT >= 19 /* KITKAT */) {
            ForgeApp.getActivity().runOnUiThread(new Runnable() {
                public void run() {
                    try {
                        final AtomicBoolean returned = new AtomicBoolean(false);
                        ValueCallback<String> cb = new ValueCallback<String>() {
                            public void onReceiveValue(String value) {
                                returned.set(true);
                                if (value.equals("\"success\"")) {
                                    if (!isLoggingNoise) {
                                        ForgeLog.d("Returned: " + returnStr);
                                    }
                                } else {
                                    javascriptReturnQueue.add(0, toReturn);
                                }
                                returning = false;
                                triggerReturn();
                            }
                        };
                        Method method = webView.getClass().getMethod("evaluateJavascript", String.class, ValueCallback.class);
                        method.invoke(webView, "window.forge && window.forge._receive && window.forge._receive("+returnStr+","+System.identityHashCode(toReturn.second)+")", cb);
                        // 500ms timeout in case returning fails.
                        new Handler(ForgeApp.getActivity().getApplicationContext().getMainLooper()).postDelayed(new Runnable() {
                            public void run() {
                                if (!returned.get()) {
                                    javascriptReturnQueue.add(0, toReturn);
                                    returning = false;
                                    triggerReturn();
                                }
                            }
                        }, 500);
                    } catch (NoSuchMethodException e) {
                        javascriptReturnQueue.add(0, toReturn);
                        returning = false;
                        return;
                    } catch (IllegalAccessException e) {
                        javascriptReturnQueue.add(0, toReturn);
                        returning = false;
                        return;
                    } catch (IllegalArgumentException e) {
                        javascriptReturnQueue.add(0, toReturn);
                        returning = false;
                        return;
                    } catch (InvocationTargetException e) {
                        javascriptReturnQueue.add(0, toReturn);
                        returning = false;
                        return;
                    }
                }
            });
        } else {
            if (reflectionReady.get(webView) == null || !reflectionReady.get(webView)) {
                // Use reflection to get references to some of the webviews inner workings.
                synchronized (reflectionReady) {
                    if (reflectionReady.get(webView) == null || !reflectionReady.get(webView)) {
                        Object wvObj = webView;
                        Object mProvider = null;

                        try {
                            Field f = wvObj.getClass().getSuperclass().getDeclaredField("mProvider");
                            f.setAccessible(true);
                            mProvider = f.get(wvObj);
                            wvObj = mProvider;
                        } catch (NoSuchFieldException e) {
                            // mProvider only exists on later android.
                            // If it doesn't exist we already have the right object
                        } catch (IllegalArgumentException e) {
                            javascriptReturnQueue.add(0, toReturn);
                            returning = false;
                            return;
                        } catch (IllegalAccessException e) {
                            javascriptReturnQueue.add(0, toReturn);
                            returning = false;
                            return;
                        }

                        try {
                            Field f = null;
                            if (mProvider != null) {
                                f = mProvider.getClass().getDeclaredField("mWebViewCore");
                            } else { // we need WebView, not ForgeWebView
                                f = wvObj.getClass().getSuperclass().getDeclaredField("mWebViewCore");
                            }
                            f.setAccessible(true);
                            wvObj = f.get(wvObj);

                            Field eventHubField = wvObj.getClass().getDeclaredField("mEventHub");
                            eventHubField.setAccessible(true);
                            Object eventHub = eventHubField.get(wvObj);
                            @SuppressWarnings("rawtypes")
                            Class eventHubClass = eventHub.getClass();

                            Field handlerField = eventHubClass.getDeclaredField("mHandler");
                            handlerField.setAccessible(true);
                            handler.put(webView, (Handler) handlerField.get(eventHub));

                            Field frameField = wvObj.getClass().getDeclaredField("mBrowserFrame");
                            frameField.setAccessible(true);
                            browserFrame.put(webView, frameField.get(wvObj));

                            callJS.put(webView, browserFrame.get(webView).getClass().getMethod("stringByEvaluatingJavaScriptFromString", String.class));
                        } catch (NoSuchFieldException e) {
                            javascriptReturnQueue.add(0, toReturn);
                            returning = false;
                            return;
                        } catch (IllegalArgumentException e) {
                            javascriptReturnQueue.add(0, toReturn);
                            returning = false;
                            return;
                        } catch (IllegalAccessException e) {
                            javascriptReturnQueue.add(0, toReturn);
                            returning = false;
                            return;
                        } catch (NoSuchMethodException e) {
                            javascriptReturnQueue.add(0, toReturn);
                            returning = false;
                            return;
                        } catch (NullPointerException e) {
                            javascriptReturnQueue.add(0, toReturn);
                            returning = false;
                            return;
                        }
                        if (handler.get(webView) == null || callJS.get(webView) == null || browserFrame.get(webView) == null) {
                            javascriptReturnQueue.add(0, toReturn);
                            returning = false;
                            return;
                        }
                        reflectionReady.put(webView, true);
                    }

                }
            }

            handler.get(webView).post(new Runnable() {
                public void run() {
                    try {
                        String value = (String)callJS.get(webView).invoke(browserFrame.get(webView), "window.forge && window.forge._receive && window.forge._receive("+returnStr+")");
                        if (value == null) {
                        } else if (value.equals("success")) {
                            ForgeLog.d("Returned: " + returnStr);
                        } else {
                            javascriptReturnQueue.add(0, toReturn);
                        }
                        returning = false;
                        triggerReturn();
                    } catch (IllegalAccessException e) {
                        javascriptReturnQueue.add(0, toReturn);
                        returning = false;
                    } catch (InvocationTargetException e) {
                        javascriptReturnQueue.add(0, toReturn);
                        returning = false;
                    }
                }
            });
        }
    }

    private static void triggerReturn() {
        boolean shouldReturn = false;
        synchronized (javascriptReturnQueue) {
            if (!returning) {
                returning = true;
                shouldReturn = true;
            }
        }
        if (shouldReturn) {
            try {
                returnNextObj();
            } catch (Exception e) {
                ForgeLog.e("Unknown error triggering queued event: " +
                           Throwables.getRootCause(e).getMessage());
                ForgeLog.e(Throwables.getStackTraceAsString(e));
            }
        }
    }

    /**
     * Add an object to the queue to return to Javascript. Notifies Javascript that the object is there to request.
     *
     * @param data
     * @hide
     */
    public static void returnObject(final ForgeWebView webView, final JsonObject data) {
        if (webView == null) {
            return;
        }
        javascriptReturnQueue.add(new Pair<ForgeWebView, JsonObject>(webView, data));
        triggerReturn();
    }

    /**
     * Get the identifier for a resource. R.string.name won't work when plugins are included in Forge
     * @param name Name of resource
     * @param type Type of resource, i.e. "string"
     * @return Resource id
     */
    public static int getResourceId(final String name, final String type) {
        return getActivity().getResources().getIdentifier(name, type, getActivity().getApplicationContext().getPackageName());
    }

    public static JsonObject configForPlugin(final String name) {
        return configForModule(name);
    }

    /**
     * Get the config specified by the user at build time for a specific plugin
     * @param name name of module
     * @return config dictionary as JsonObject
     */
    public static JsonObject configForModule(String name) {
        if (moduleMapping.has(name)) {
            name = moduleMapping.get(name).getAsString();
            if (appConfig.has("modules")
                    && appConfig.getAsJsonObject("modules").has(name)
                    && appConfig.getAsJsonObject("modules").getAsJsonObject(name).has("config")) {
                return appConfig.getAsJsonObject("modules").getAsJsonObject(name).getAsJsonObject("config");
            }
        }
        return new JsonObject();
    }

    /**
     * @hide
     */
    @Override
    public Object getSystemService(String name) {
        Object ret = super.getSystemService(name);
        if (ret != null) {
            return ret;
        } else {
            return ForgeApp.nativeEvent("getSystemService", new Object[] { name });
        }
    }

    public static boolean flag(String name) {
        if (appConfig.has("flags") && appConfig.getAsJsonObject("flags").has(name)) {
            return appConfig.getAsJsonObject("flags").get(name).getAsBoolean();
        }
        return false;
    }

}
