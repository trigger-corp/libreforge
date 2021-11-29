package io.trigger.forge.android.core;

import java.lang.reflect.Method;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.Hashtable;
import java.util.List;
import java.util.Stack;
import java.util.concurrent.ConcurrentHashMap;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.content.res.Configuration;
import android.graphics.Bitmap;
import android.graphics.Point;
import android.graphics.Rect;
import android.graphics.drawable.ColorDrawable;
import android.net.Uri;
import android.net.http.SslCertificate;
import android.net.http.SslError;
import android.os.Build;
import android.os.Bundle;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import android.util.DisplayMetrics;
import android.util.TypedValue;
import android.view.ContextMenu;
import android.view.ContextMenu.ContextMenuInfo;
import android.view.Display;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.Menu;
import android.view.MenuItem;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewTreeObserver;
import android.view.WindowManager.LayoutParams;
import android.view.animation.Animation;
import android.view.animation.Animation.AnimationListener;
import android.view.animation.LinearInterpolator;
import android.view.animation.TranslateAnimation;
import android.view.inputmethod.InputMethodManager;
import android.webkit.ConsoleMessage;
import android.webkit.CookieManager;
import android.webkit.CookieSyncManager;
import android.webkit.GeolocationPermissions;
import android.webkit.JsResult;
import android.webkit.SslErrorHandler;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebStorage;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.RelativeLayout;
import android.widget.TextView;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

/**
 * The Forge subclass of Activity. The entry point to the application, contains references to the root layout and webView objects.
 */
public class ForgeActivity extends Activity {
    /**
     * The main webView, used to display the app.
     */
    public ForgeWebView webView;
    private ForgeWebView webViewDestroy;

    /**
     * The root layout of the application, can be manipulated to place other views above or below the webview.
     */
    public LinearLayout mainLayout;
    private ViewGroup mainViewGroup;
    public LinearLayout.LayoutParams navigationBarLayoutParams;

    private Hashtable<Integer, ForgeIntentResultHandler> intentHandlers = new Hashtable<Integer, ForgeIntentResultHandler>();
    private int intentHandlerId = 80000;
    private Stack<Runnable> resumeCallbacks = new Stack<Runnable>();

    /**
     * Whether or not a modal view is currently being displayed over the main view
     */
    public boolean hasModalView = false;

    /**
     * @hide
     */
    private Runnable videoBackPressed = null;

    /**
     * @hide
     */
    public ForgeActivity() {
    }

    /**
     * @hide
     */
    @Override
    public void onCreate(Bundle savedInstanceState) {
        ForgeApp.setActivity(this);

        // check flags
        flag_android_workaround_transparent_statusbar_keyboard_bug = ForgeApp.flag("android_workaround_transparent_statusbar_keyboard_bug");

        // Create Main Layout
        mainLayout = new LinearLayout(this);
        mainLayout.setOrientation(LinearLayout.VERTICAL);
        mainLayout.setLayoutParams(new ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        // Create NavigationBar
        RelativeLayout navigationBar = new RelativeLayout(this);
        navigationBar.setLayoutParams(new ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                                      Math.round(ForgeConstant.getNavigationBarHeightStatic())));
        navigationBar.setGravity(Gravity.CENTER);
        navigationBar.setBackgroundDrawable(new ColorDrawable(0xFFEEEEEE));
        TextView navigationBarTitle = new TextView(this);
        if (ForgeApp.appConfig.has("name")) {
            navigationBarTitle.setText(ForgeApp.appConfig.get("name").getAsString());
        }
        navigationBarTitle.setTextColor(0xFF000000);
        navigationBarTitle.setTextSize(TypedValue.COMPLEX_UNIT_PX, ForgeConstant.getNavigationBarTextHeightStatic());
        navigationBarTitle.setGravity(Gravity.CENTER);
        //RelativeLayout.LayoutParams layoutParams = new RelativeLayout.LayoutParams(10000, 10000);
        //navigationBar.addView(navigationBarTitle, layoutParams);
        navigationBar.addView(navigationBarTitle);
        ForgeViewController.navigationBar = navigationBar;
        ForgeViewController.navigationBarTitle = navigationBarTitle;
        navigationBarLayoutParams = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                                                                  Math.round(ForgeConstant.getNavigationBarHeightStatic()));
        mainLayout.addView(navigationBar, navigationBarLayoutParams);
        mainLayout.setBackgroundColor(0xFFFFFFFF);

        // Create Webview
        webViewDestroy = webView = new ForgeWebView(this);
        //mainLayout.addView(webView, 0, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT, 1));
        mainLayout.addView(webView, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT, 1));

        // Create TabBar
        LinearLayout tabBar = new LinearLayout(this);
        tabBar.setOrientation(LinearLayout.HORIZONTAL);
        tabBar.setLayoutParams(new ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                               Math.round(ForgeConstant.getTabBarSizeStatic())));
        tabBar.setGravity(Gravity.CENTER);
        tabBar.setBackgroundDrawable(new ColorDrawable(0xFFEEEEEE));
        ForgeViewController.tabBar = tabBar;
        mainLayout.addView(tabBar);
        mainLayout.setBackgroundColor(0xFFFFFFFF);

        // Create Main View Group
        mainViewGroup = new FrameLayout(this);
        mainViewGroup.addView(mainLayout, 0);

        // setFitsSystemWindows
        /*boolean fitsSystemWindows = false;
        mainLayout.setFitsSystemWindows(fitsSystemWindows);
        navigationBar.setFitsSystemWindows(fitsSystemWindows);
        navigationBarTitle.setFitsSystemWindows(fitsSystemWindows);
        webView.setFitsSystemWindows(fitsSystemWindows);
        tabBar.setFitsSystemWindows(fitsSystemWindows);
        mainViewGroup.setFitsSystemWindows(fitsSystemWindows);*/

        // enable remote debugging for chrome webview
        if (Build.VERSION.SDK_INT >= 19 /* KITKAT */
            && ForgeApp.appConfig.has("core")
            && ForgeApp.appConfig.getAsJsonObject("core").has("android")
            && ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("android").has("remote_debugging")
            && ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("android").get("remote_debugging").getAsBoolean()) {
            WebView.setWebContentsDebuggingEnabled(true);
            ForgeLog.i("Android remote debugging enabled.");
        } else {
            ForgeLog.i("Android remote debugging disabled.");
        }

        // Depending on Android version handle Javascript errors in the best way
        // possible.
        final ForgeActivity currentActivity = this;
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.FROYO) {
            webView.setWebChromeClient(new WebChromeClient() {
                @Override
                public boolean onJsAlert(WebView view, String url, String message, JsResult result) {
                    return super.onJsAlert(view, url, message, result);
                }

                @Override
                public void onConsoleMessage(String message, int lineNumber, String sourceID) {
                    if (webView != null && !message.startsWith(">") && !(message.startsWith("[") && !message.endsWith("]"))) {
                        webView.loadUrl("javascript:console.error('> " + (message + " -- From line " + lineNumber + " of " + sourceID).replace("\\", "\\\\").replace("'", "\\'") + "')");
                        ForgeLog.e(message + " -- From line " + lineNumber + " of " + sourceID);
                    }
                }

                @Override
                public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) {
                    callback.invoke(origin, true, false);
                }

                @Override
                public void onExceededDatabaseQuota(String url, String databaseIdentifier, long currentQuota, long estimatedSize, long totalUsedQuota, WebStorage.QuotaUpdater quotaUpdater) {
                    quotaUpdater.updateQuota(estimatedSize * 2);
                }
            });
        } else {
            webView.setWebChromeClient(new WebChromeClient() {
                private LinearLayout layout = null;

                @Override
                public boolean onJsAlert(WebView view, String url, String message, JsResult result) {
                    return super.onJsAlert(view, url, message, result);
                }

                @Override
                public boolean onConsoleMessage(ConsoleMessage cm) {
                    if (webView != null && !cm.message().startsWith(">") && !(cm.message().startsWith("[") && !cm.message().endsWith("]"))) {
                        webView.loadUrl("javascript:console.error('> " + (cm.message() + " -- From line " + cm.lineNumber() + " of " + cm.sourceId()).replace("\\", "\\\\").replace("'", "\\'") + "')");
                        ForgeLog.e(cm.message() + " -- From line " + cm.lineNumber() + " of " + cm.sourceId());
                    }
                    return true;
                }

                @Override
                public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) {
                    callback.invoke(origin, true, false);
                }

                @Override
                public void onExceededDatabaseQuota(String url, String databaseIdentifier, long currentQuota, long estimatedSize, long totalUsedQuota, WebStorage.QuotaUpdater quotaUpdater) {
                    quotaUpdater.updateQuota(estimatedSize * 2);
                }

                @Override
                public void onShowCustomView(View view,	final CustomViewCallback callback) {
                    layout = new LinearLayout(currentActivity);
                    layout.setOrientation(LinearLayout.VERTICAL);
                    layout.setLayoutParams(new ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
                    layout.setBackgroundColor(0xFF000000);

                    LayoutParams params = new LayoutParams(-1, -1, 1);
                    view.setLayoutParams(params);
                    layout.addView(view);
                    addModalView(layout);

                    videoBackPressed = new Runnable() {
                        public void run() {
                            callback.onCustomViewHidden();
                            onHideCustomView();
                        }
                    };
                }

                @Override
                public void onHideCustomView() {
                    videoBackPressed = null;
                    if (layout != null) {
                        removeModalView(layout, new Runnable() {
                            public void run() {
                                layout = null;
                            }
                        });
                    }
                }

                /*@Override
                public void onProgressChanged(WebView view, int newProgress) {
                    ForgeLog.d("Progess: " + newProgress);
                }*/

                @Override
                public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, WebChromeClient.FileChooserParams fileChooserParams) {
                    return ForgeViewController.onShowFileChooser(webView, filePathCallback, fileChooserParams);
                }
            });
        }

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                ForgeLog.w("[FORGE WebView error] " + description);
            }

            @Override
            public void onReceivedSslError (WebView view, SslErrorHandler handler, SslError error) {
                // support self-signed certificates for localhost
                try {
                    URL url = new URL(error.getUrl());
                    SslCertificate certificate = error.getCertificate();

                    String host = url.getHost();
                    String cname = certificate.getIssuedTo().getCName();

                    if ((cname.equalsIgnoreCase("localhost") ||
                         cname.equalsIgnoreCase("127.0.0.1")) &&
                        (host.equalsIgnoreCase("localhost") ||
                         host.equalsIgnoreCase("127.0.0.1"))) {
                        ForgeLog.d("[FORGE WebView] Trusting self-signed certificate for localhost");
                        handler.proceed();

                    } else {
                        String message = "Unknown SSL Certificate error";
                        switch (error.getPrimaryError()) {
                            case SslError.SSL_UNTRUSTED:
                                message = "The certificate authority is not trusted";
                                break;
                            case SslError.SSL_EXPIRED:
                                message = "The certificate has expired";
                                break;
                            case SslError.SSL_IDMISMATCH:
                                message = "The certificate Hostname mismatch";
                                break;
                            case SslError.SSL_NOTYETVALID:
                                message = "The certificate is not yet valid";
                                break;
                        }
                        ForgeLog.e("[FORGE WebView SSL error] " + message + ": " + error.toString());
                        ForgeLog.e("[FORGE WebView SSL error] CN=" + cname + " HOST=" + host);
                        handler.cancel();
                    }
              } catch (Exception e) {
                    ForgeLog.e("[FORGE WebView error] " + e.getLocalizedMessage());
                    handler.cancel();
                }
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                // track loading
                if (!loadingFinished) {
                    loadingRedirect = true;
                }
                loadingFinished = false;

                // Make sure nothing is cached
                view.clearCache(true);

                if (url.startsWith("content://" + currentActivity.getApplicationContext().getPackageName())) {
                    // Local file, allow the WebView to handle it.
                    ForgeLog.i("Webview switching to internal URL: " + url);
                    return false;
                } else if (url.startsWith("about:")) {
                    // Ignore about:* URLs
                    return true;
                }

                // Always allow localhost
                if (url.startsWith("https://localhost") || url.startsWith("https://127.0.0.1") ||
                    url.startsWith("http://localhost") || url.startsWith("http://127.0.0.1")) {
                    ForgeLog.i("Webview switching to trusted internal URL: " + url);
                    return false;
                }

                // Check against trusted_urls:
                if (ForgeApp.appConfig.has("core")
                        && ForgeApp.appConfig.getAsJsonObject("core").has("general")
                        && ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").has("trusted_urls")) {
                    JsonArray trusted_urls = ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").getAsJsonArray("trusted_urls");
                    for (JsonElement pattern : trusted_urls) {
                        if (ForgeUtil.urlMatchesPattern(url, pattern.getAsString())) {
                            ForgeLog.i("Webview switching to trusted URL: " + url);
                            return false;
                        }
                    }
                }

                // See if URL is a request for the live server
                if (ForgeApp.appConfig.has("core")
                        && ForgeApp.appConfig.getAsJsonObject("core").has("general")
                        && ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").has("live")
                        && ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").getAsJsonObject("live").has("enabled")
                        && ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").getAsJsonObject("live").get("enabled").getAsBoolean()) {
                    String liveUrl = ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").getAsJsonObject("live").get("url").getAsString();
                    try {
                        return !(new URL(url)).getHost().equals((new URL(liveUrl)).getHost());
                    } catch (MalformedURLException e) {
                        ForgeLog.e("Malformed live url: " + e.getMessage());
                    }
                }

                // Some other URI scheme, let the phone handle it if possible
                Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                intent.addCategory(Intent.CATEGORY_BROWSABLE);
                final PackageManager packageManager = currentActivity.getPackageManager();
                List<ResolveInfo> list = packageManager.queryIntentActivities(intent, 0);
                if (list.size() > 0) {
                    // Intent exists, invoke it.
                    ForgeLog.i("Allowing another Android app to handle URL: " + url);
                    currentActivity.startActivity(intent);
                } else {
                    ForgeLog.w("Attempted to open a URL which could not be handled: " + url);
                }

                return true;
            }

            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
                loadingFinished = false;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                if (!loadingRedirect) {
                    loadingFinished = true;
                    // update safe area insets
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT_WATCH) {
                        webView.requestApplyInsets();
                    }
                } else {
                    loadingRedirect = false;
                }
            }

            boolean loadingFinished = true;
            boolean loadingRedirect = false;
        });

        // Change some default settings to be more sensible.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.HONEYCOMB
                && !((ForgeApp.appConfig.has("core")
                        && ForgeApp.appConfig.getAsJsonObject("core").has("android")
                        && ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("android").has("disable_ics_acceleration")
                        && ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("android").get("disable_ics_acceleration").getAsBoolean())
                && (Build.VERSION.SDK_INT == Build.VERSION_CODES.ICE_CREAM_SANDWICH || Build.VERSION.SDK_INT == Build.VERSION_CODES.ICE_CREAM_SANDWICH_MR1))) {
            getWindow().setFlags(LayoutParams.FLAG_HARDWARE_ACCELERATED, LayoutParams.FLAG_HARDWARE_ACCELERATED);
            ForgeLog.i("Android hardware acceleration enabled.");
        } else {
            ForgeLog.i("Android hardware acceleration disabled.");
        }
        WebSettings webSettings = webView.getSettings();

        webSettings.setJavaScriptEnabled(true);
        webSettings.setSupportZoom(false);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.ECLAIR_MR1) {
            webSettings.setDomStorageEnabled(true);
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            webSettings.setMediaPlaybackRequiresUserGesture(false);
        }

        // remove content & protocol restrictions where possible
        webSettings.setAllowContentAccess(true);
        webSettings.setAllowFileAccess(true);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN) {
            webSettings.setAllowFileAccessFromFileURLs(true);
            webSettings.setAllowUniversalAccessFromFileURLs(true); // Allow web workers access to file URL's
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            webSettings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }

        webSettings.setGeolocationEnabled(true);
        webSettings.setDatabaseEnabled(true);
        String databasePath = getApplicationContext().getDir("database", Context.MODE_PRIVATE).getPath();
        webSettings.setDatabasePath(databasePath);
        // Don't highlight selected elements
        // webSettings.setLightTouchEnabled(true);

        // Scroll bar shouldn't actually take up space
        webView.setScrollBarStyle(View.SCROLLBARS_INSIDE_OVERLAY);

        // Disable overscroll if used
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.GINGERBREAD) {
            // Use reflection to prevent errors on older devices
            Class<?> viewCls = webView.getClass();
            try {
                Method m = viewCls.getMethod("setOverScrollMode", new Class[] { int.class });
                int OVER_SCROLL_NEVER = (Integer) viewCls.getField("OVER_SCROLL_NEVER").get(webView);
                m.invoke(webView, OVER_SCROLL_NEVER);
            } catch (Exception e) {
            }
        }

        // Allow JavaScript to call Java code.
        webView.addJavascriptInterface(new ForgeJSBridge(webView), "__forge");

        // Configure caching.
        boolean cache_enabled =
                (ForgeApp.appConfig.has("core")
                && ForgeApp.appConfig.getAsJsonObject("core").has("general")
                && ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").has("cache")
                && ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").getAsJsonObject("cache").has("enabled"))
                ?  ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").getAsJsonObject("cache").get("enabled").getAsBoolean()
                : false;
        if (cache_enabled == true) {
            webSettings.setCacheMode(WebSettings.LOAD_DEFAULT);
        } else {
            webSettings.setCacheMode(WebSettings.LOAD_NO_CACHE);
        }
        webView.clearCache(true);

        // Finally show URL in the WebView.
        loadInitialPage();

        // Keepalive causes problems with some HTTPS servers.
        System.setProperty("http.keepAlive", "false");

        // Enable persistent cookies by default
        CookieManager cookieManager = CookieManager.getInstance();
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) {
            CookieSyncManager.createInstance(this);
        }
        cookieManager.setAcceptCookie(true);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            cookieManager.setAcceptThirdPartyCookies(ForgeApp.getActivity().webView, true);
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.HONEYCOMB) {
            CookieManager.setAcceptFileSchemeCookies(true);
        }

        // Themes
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.HONEYCOMB_MR2) {
            setTheme(android.R.style.Theme_NoTitleBar);
        } else {
            setTheme(android.R.style.Theme_Holo_Light_NoActionBar);
        }

        ForgeViewController.onCreate(savedInstanceState, mainViewGroup);

        ForgeApp.nativeEvent("onCreate", new Object[] { savedInstanceState });

        // Keyboard listener
        if (!keyboardListenerAttached) {
            mainViewGroup.getViewTreeObserver().addOnGlobalLayoutListener(keyboardListener);
            keyboardListenerAttached = true;
        }

        // Some methods need to be called before this -> do it last.
        setContentView(mainViewGroup);

        super.onCreate(savedInstanceState);
    }

    /**
     * @hide
     */
    public void loadInitialPage() {
        // check if we are in Forge "live" mode
        if (ForgeApp.appConfig.has("core")
                && ForgeApp.appConfig.getAsJsonObject("core").has("general")
                && ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").has("live")
                && ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").getAsJsonObject("live").has("enabled")
                && ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").getAsJsonObject("live").get("enabled").getAsBoolean()) {
            String url = ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").getAsJsonObject("live").get("url").getAsString();
            gotoUrl(url);
            ForgeLog.d("Loading live page in webview: " + url);
            return;
        }

        // check if a module is handling it
        Boolean moduleRet = (Boolean)ForgeApp.nativeEvent("onLoadInitialPage", new Object[] { webView });
        if (moduleRet != null) {
            ForgeLog.d("Loading initial page via module.");
            return;
        }

        // load from local assets directory
        gotoUrl("content://" + getApplicationContext().getPackageName() + "/src/index.html");
        ForgeLog.d("Loading initial page in webview.");
    }

    /**
     * @hide
     */
    @Override
    protected void onNewIntent(Intent intent) {
        ForgeApp.nativeEvent("onNewIntent", new Object[] { intent });
        super.onNewIntent(intent);
    }

    /**
     * @hide
     */
    @Override
    protected void onPostCreate(Bundle savedInstanceState) {
        ForgeApp.nativeEvent("onPostCreate", new Object[] { savedInstanceState });
        super.onPostCreate(savedInstanceState);
    }

    /**
     * @hide
     */
    @Override
    public void onStop() {
        CookieSyncManager.getInstance().stopSync();
        CookieSyncManager.getInstance().sync();

        if (webView != null) {
            ForgeLog.i("Pausing webview while application not focussed.");
            webView.pauseTimers();
        }

        ForgeApp.nativeEvent("onStop", new Object[] { });
        super.onStop();
    }

    /**
     * @hide
     */
    @Override
    public void onStart() {
        CookieSyncManager.getInstance().startSync();

        while (!resumeCallbacks.empty()) {
            resumeCallbacks.pop().run();
        }
        if (webView != null) {
            ForgeLog.i("Application in focus, resuming webview.");
            webView.resumeTimers();
        }

        ForgeApp.nativeEvent("onStart", new Object[] { });
        super.onStart();
    }

    /**
     * @hide
     */
    @Override
    protected void onDestroy() {
        if (keyboardListenerAttached) {
            mainViewGroup.getViewTreeObserver().removeGlobalOnLayoutListener(keyboardListener);
        }

        mainLayout.removeAllViews();
        webViewDestroy.destroy();
        webViewDestroy = null;

        ForgeApp.nativeEvent("onDestroy", new Object[] { });
        super.onDestroy();
    }

    /**
     * @hide
     */
    @Override
    protected void onRestart() {
        ForgeApp.nativeEvent("onRestart", new Object[] { });
        super.onRestart();
    }

    /**
     * @hide
     */
    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        final Configuration configuration = newConfig;

        ForgeViewController.onConfigurationChanged(configuration, new Runnable() {
            @Override
            public void run() {
            JsonObject result = new JsonObject();
                if (configuration.orientation == Configuration.ORIENTATION_PORTRAIT) {
                result.addProperty("orientation", "portrait");
                } else if (configuration.orientation == Configuration.ORIENTATION_LANDSCAPE) {
                result.addProperty("orientation", "landscape");
            }
            ForgeApp.event("internal.orientationChange", result);
                ForgeApp.nativeEvent("onConfigurationChanged", new Object[]{configuration});
        }
        });

        super.onConfigurationChanged(configuration);
    }

    /**
     * @hide
     */
    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (videoBackPressed != null) {
            if (keyCode == KeyEvent.KEYCODE_BACK) {
                videoBackPressed.run();
                return false;
            } else {
                return super.onKeyDown(keyCode, event);
            }
        }

        Boolean moduleRet = (Boolean) ForgeApp.nativeEvent("onKeyDown", new Object[] { keyCode, event });
        if (moduleRet != null) {
            return moduleRet.booleanValue();
        } else {
            return super.onKeyDown(keyCode, event);
        }
    }

    /**
     * @hide
     */
    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        ForgeIntentResultHandler handler = intentHandlers.get(requestCode);
        if (handler != null) {
            ForgeLog.i("Handling returned result from external intent (camera, address book, etc).");
            handler.result(requestCode, resultCode, data);
            unregisterIntentHandler(requestCode);
        } else if (requestCode >= 80000 && requestCode <= 81000) {
            ForgeLog.e("Unhandled Forge intent result, this was probably caused by the app being restarted while an intent was being completed such as using the camera.");
        } else {
            ForgeLog.i("Unhandled intent result, may have been handled by a 3rd party (e.g. Facebook).");
        }

        ForgeApp.nativeEvent("onActivityResult", new Object[] { requestCode, resultCode, data });
    }

    /**
     * Load a specific URL in the webView
     * @param url Absolute url to load
     */
    public void gotoUrl(final String url) {
        ForgeApp.getActivity().runOnUiThread(new Runnable() {
            public void run() {
                webView.clearCache(true);
                webView.loadUrl(url);
            }
        });
    }

    /**
     * @hide
     */
    public int registerIntentHandler(ForgeIntentResultHandler handler) {
        intentHandlers.put(intentHandlerId, handler);
        return intentHandlerId++;
    }

    private void unregisterIntentHandler(int requestCode) {
        intentHandlers.remove(requestCode);
    }

    /**
     * Add an animate in a modal view over the top of the webView.
     * @param view View to add, should be ready to display.
     */
    public void addModalView(View view) {
        mainViewGroup.addView(view);
        Animation upFromBottom = new TranslateAnimation(Animation.RELATIVE_TO_PARENT, 0.0f, Animation.RELATIVE_TO_PARENT, 0.0f, Animation.RELATIVE_TO_PARENT, 1.0f, Animation.RELATIVE_TO_PARENT, 0.0f);
        upFromBottom.setDuration(250);
        upFromBottom.setInterpolator(new LinearInterpolator());
        view.startAnimation(upFromBottom);
        mainViewGroup.bringChildToFront(view);
        hasModalView = true;
    }

    /**
     * Remove a modal view added with addModalView.
     * @param view View to remove.
     * @param callback Callback when view has been entirely removed from the display.
     */
    public void removeModalView(final View view, final Runnable callback) {
        // Clear current focus in case it is set to an element in the modal view
        View currentFocus = this.getCurrentFocus();
        if (currentFocus != null) {
            currentFocus.clearFocus();
        }

        // Hide the keyboard or weird stuff can happen.
        InputMethodManager imm = (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);
        imm.hideSoftInputFromWindow(mainLayout.getWindowToken(), 0);

        Animation downFromTop = new TranslateAnimation(Animation.RELATIVE_TO_PARENT, 0.0f, Animation.RELATIVE_TO_PARENT, 0.0f, Animation.RELATIVE_TO_PARENT, 0.0f, Animation.RELATIVE_TO_PARENT, 1.0f);
        downFromTop.setDuration(250);
        downFromTop.setInterpolator(new LinearInterpolator());
        downFromTop.setAnimationListener(new AnimationListener() {
            public void onAnimationEnd(Animation animation) {
                try {
                    mainViewGroup.removeView(view);
                    mainViewGroup.bringChildToFront(mainLayout);
                    webView.requestFocus(View.FOCUS_DOWN);
                    callback.run();
                } catch (Exception e) {
                    ForgeLog.w("Unknown problem closing modal view.");
                }
            }

            public void onAnimationRepeat(Animation animation) {
            }

            public void onAnimationStart(Animation animation) {
            }
        });
        view.startAnimation(downFromTop);
        hasModalView = false;
    }

    /**
     * Add a callback for the next time the app is resumed. Useful when triggering an intent with no result to know when the user has returned to the Forge app.
     * @param callback Called on next app resume.
     */
    public void addResumeCallback(Runnable callback) {
        resumeCallbacks.push(callback);
    }

    /**
     * @hide
     */
    @Override
    public boolean onContextItemSelected(MenuItem item) {
        Boolean moduleResult = (Boolean) ForgeApp.nativeEvent(
                "onContextItemSelected", new Object[] { item });
        if (moduleResult == null) {
            return super.onContextItemSelected(item);
        } else {
            return moduleResult;
        }
    }

    /**
     * @hide
     */
    @Override
    public void onContextMenuClosed(Menu menu) {
        ForgeApp.nativeEvent("onContextMenuClosed", new Object[] { menu });
        super.onContextMenuClosed(menu);
    }

    /**
     * @hide
     */
    @Override
    public void onCreateContextMenu(ContextMenu menu, View v,
            ContextMenuInfo menuInfo) {
        ForgeApp.nativeEvent("onCreateContextMenu", new Object[] { menu, v,
                menuInfo });
        super.onCreateContextMenu(menu, v, menuInfo);
    }

    /**
     * @hide
     */
    @Override
    public boolean onKeyLongPress(int keyCode, KeyEvent event) {
        Boolean moduleResult = (Boolean) ForgeApp.nativeEvent("onKeyLongPress",
                new Object[] { keyCode, event });
        if (moduleResult == null) {
            return super.onKeyLongPress(keyCode, event);
        } else {
            return moduleResult;
        }
    }

    /**
     * @hide
     */
    @Override
    public boolean onKeyMultiple(int keyCode, int repeatCount, KeyEvent event) {
        Boolean moduleResult = (Boolean) ForgeApp.nativeEvent("onKeyMultiple",
                new Object[] { keyCode, repeatCount, event });
        if (moduleResult == null) {
            return super.onKeyMultiple(keyCode, repeatCount, event);
        } else {
            return moduleResult;
        }
    }

    /**
     * @hide
     */
    @Override
    public boolean onKeyUp(int keyCode, KeyEvent event) {
        Boolean moduleResult = (Boolean) ForgeApp.nativeEvent("onKeyUp",
                new Object[] { keyCode, event });
        if (moduleResult == null) {
            return super.onKeyUp(keyCode, event);
        } else {
            return moduleResult;
        }
    }

    /**
     * @hide
     */
    @Override
    public void onLowMemory() {
        ForgeApp.nativeEvent("onLowMemory", new Object[] {});
        super.onLowMemory();
    }

    /**
     * @hide
     */
    @Override
    public boolean onSearchRequested() {
        Boolean moduleResult = (Boolean) ForgeApp.nativeEvent(
                "onSearchRequested", new Object[] {});
        if (moduleResult == null) {
            return super.onSearchRequested();
        } else {
            return moduleResult;
        }
    }

    /**
     * @hide
     */
    @Override
    public boolean onTouchEvent(MotionEvent event) {
        Boolean moduleResult = (Boolean) ForgeApp.nativeEvent("onTouchEvent",
                new Object[] { event });
        if (moduleResult == null) {
            return super.onTouchEvent(event);
        } else {
            return moduleResult;
        }
    }

    /**
     * @hide
     */
    @Override
    public boolean onTrackballEvent(MotionEvent event) {
        Boolean moduleResult = (Boolean) ForgeApp.nativeEvent(
                "onTrackballEvent", new Object[] { event });
        if (moduleResult == null) {
            return super.onTrackballEvent(event);
        } else {
            return moduleResult;
        }
    }

    /**
     * @hide
     */
    @Override
    public void onUserInteraction() {
        ForgeApp.nativeEvent("onUserInteraction", new Object[] {});
        super.onUserInteraction();
    }

    /**
     * @hide
     */
    @Override
    public void onWindowAttributesChanged(LayoutParams params) {
        ForgeApp.nativeEvent("onWindowAttributesChanged",
                new Object[] { params });
        super.onWindowAttributesChanged(params);
    }

    /**
     * @hide
     */
    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        ForgeApp.nativeEvent("onWindowFocusChanged", new Object[] { hasFocus });
        super.onWindowFocusChanged(hasFocus);
    }

    /**
     * @hide
     */
    @Override
    protected void onPostResume() {
        ForgeApp.nativeEvent("onPostResume", new Object[] {});
        super.onPostResume();
    }

    /**
     * @hide
     */
    @Override
    protected void onResume() {
        ForgeApp.nativeEvent("onResume", new Object[] {});
        super.onResume();
    }

    /**
     * @hide
     */
    @Override
    protected void onPause() {
        ForgeApp.nativeEvent("onPause", new Object[] {});
        super.onPause();
    }

    /**
     * @hide
     */
    @Override
    protected void onUserLeaveHint() {
        ForgeApp.nativeEvent("onUserLeaveHint", new Object[] {});
        super.onUserLeaveHint();
    }

    /**
     * @hide
     */
    @Override
    protected void onSaveInstanceState(Bundle outState) {
        ForgeApp.nativeEvent("onSaveInstanceState", new Object[] { outState });
        super.onSaveInstanceState(outState);
    }

    /**
     * @hide
     */
    @Override
    protected void onRestoreInstanceState(Bundle savedInstanceState) {
        ForgeApp.nativeEvent("onRestoreInstanceState",
                new Object[] { savedInstanceState });
        super.onRestoreInstanceState(savedInstanceState);
    }

    /**
     * @hide
     */
    @Override
    public void onRequestPermissionsResult(int requestCode, String permissions[], int[] grantResults) {
        final EventAccessBlock block = permissionRequestBlocks.get(requestCode);
        if (block == null) {
            return;
        }
        permissionRequestBlocks.remove(requestCode);
        block.run(grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED);

        ForgeApp.nativeEvent("onRequestPermissionsResult", new Object[] { requestCode, permissions, grantResults });
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
    }

    /**
     * Request a permission with a completion handler
     *
     * @param permission
     * @param block
     */
    public void requestPermission(final String permission, final EventAccessBlock block) {
        try {
            if (ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED) {
                block.run(true);
                return;
            }
            requestId++;
            permissionRequestBlocks.put(requestId, block);
            if (Build.VERSION.SDK_INT >= 23) {
                ActivityCompat.requestPermissions(this, new String[]{permission}, requestId);
            } else {
                block.run(true);
            }
        } catch (IllegalArgumentException e) {
            // permission support is spotty across Android API versions but
            // for consistency with the check & request API's we unfortunately
            // have to claim that the permission was denied :-/
            ForgeLog.w("Requested unknown permission: " + permission);
            ForgeLog.w(e.getLocalizedMessage());
            block.run(false);
        }
    }

    public interface EventAccessBlock {
        void run(boolean granted);
    }
    private ConcurrentHashMap<Integer, EventAccessBlock> permissionRequestBlocks = new ConcurrentHashMap<Integer, EventAccessBlock>();
    private int requestId = 1;

    // borrowed from: https://github.com/ionic-team/cordova-plugin-ionic-keyboard/blob/master/src/android/IonicKeyboard.java
    private ViewTreeObserver.OnGlobalLayoutListener keyboardListener = new ViewTreeObserver.OnGlobalLayoutListener() {
        float previousHeightDiff = 0.0f;

        @Override
        public void onGlobalLayout() {
            DisplayMetrics displayMetrics = new DisplayMetrics();
            ForgeApp.getActivity().getWindowManager().getDefaultDisplay().getMetrics(displayMetrics);
            final float density = displayMetrics.density;

            Rect r = new Rect();
            mainViewGroup.getWindowVisibleDisplayFrame(r);

            // cache properties for later use
            int rootViewHeight = mainViewGroup.getRootView().getHeight();
            int resultBottom = r.bottom;

            // calculate screen height differently for android versions >= 21: Lollipop 5.x, Marshmallow 6.x
            // beware of nexus 5: http://stackoverflow.com/a/29257533/3642890
            int screenHeight;

            if (Build.VERSION.SDK_INT >= 21) {
                Display display = ForgeApp.getActivity().getWindowManager().getDefaultDisplay();
                Point size = new Point();
                display.getSize(size);
                screenHeight = size.y;
            } else {
                screenHeight = rootViewHeight;
            }

            float heightDiff = screenHeight - resultBottom;

            float pixelHeightDiff = heightDiff / density;
            if (pixelHeightDiff > 100.0f && pixelHeightDiff != previousHeightDiff) { // if more than 100 pixels, its probably a keyboard...
                onKeyboardDidShow(heightDiff);
            } else if ( pixelHeightDiff != previousHeightDiff && ( previousHeightDiff - pixelHeightDiff ) > 100 ){
                onKeyboardDidHide();
            }
            previousHeightDiff = pixelHeightDiff;
        }
    };
    private boolean keyboardListenerAttached = false;

    protected void onKeyboardDidShow(float keyboardHeight) {
        if (flag_android_workaround_transparent_statusbar_keyboard_bug && (Build.VERSION.SDK_INT > Build.VERSION_CODES.KITKAT)) {
            adjustFrameForKeyboard((int)keyboardHeight);
        }
        ForgeApp.nativeEvent("onKeyboardDidShow", new Object[] { keyboardHeight });
    }

    protected void onKeyboardDidHide() {
        if (flag_android_workaround_transparent_statusbar_keyboard_bug && (Build.VERSION.SDK_INT > Build.VERSION_CODES.KITKAT)) {
            adjustFrameForKeyboard(0);
        }
        ForgeApp.nativeEvent("onKeyboardDidHide", new Object[] { });
    }

    // Workaround for statusbar: transparent bug which prevents soft keyboard from scrolling hidden inputs into view
    // https://stackoverflow.com/questions/19897422/
    protected void adjustFrameForKeyboard(int keyboardHeight) { // restore layout after keyboard has been hidden
        if (keyboardHeight == 0 && preShowKeyboardContentInsets != null) {
            mainLayout.setPadding(preShowKeyboardContentInsets.left,
                    preShowKeyboardContentInsets.top,
                    preShowKeyboardContentInsets.right,
                    preShowKeyboardContentInsets.bottom);
            preShowKeyboardContentInsets = null;

        } else if (keyboardHeight == 0) { // content insets were never cached for some reason
            mainLayout.setPadding(0, 0, 0, 0);

        } else if (preShowKeyboardContentInsets == null) { // keyboard is being shown for the first time
            preShowKeyboardContentInsets = new Rect();
            preShowKeyboardContentInsets.left = mainLayout.getPaddingLeft();
            preShowKeyboardContentInsets.top = mainLayout.getPaddingTop();
            preShowKeyboardContentInsets.right = mainLayout.getPaddingRight();
            preShowKeyboardContentInsets.bottom = mainLayout.getPaddingBottom();
            mainLayout.setPadding(preShowKeyboardContentInsets.left,
                    preShowKeyboardContentInsets.top,
                    preShowKeyboardContentInsets.right,
                    keyboardHeight);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
                webView.evaluateJavascript("document.activeElement.scrollIntoViewIfNeeded();", null);
            }

        } else { // if we switch keyboard types while the keyboard is open
            mainLayout.setPadding(preShowKeyboardContentInsets.left,
                                  preShowKeyboardContentInsets.top,
                                  preShowKeyboardContentInsets.right,
                                  keyboardHeight);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
                webView.evaluateJavascript("document.activeElement.scrollIntoViewIfNeeded();", null);
            }
        }
    }
    private boolean flag_android_workaround_transparent_statusbar_keyboard_bug = false;
    private Rect preShowKeyboardContentInsets = null;

}
