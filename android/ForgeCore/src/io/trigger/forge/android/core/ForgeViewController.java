package io.trigger.forge.android.core;

import android.content.Intent;
import android.content.res.Configuration;
import android.graphics.RectF;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;

import androidx.core.view.DisplayCutoutCompat;
import androidx.core.view.OnApplyWindowInsetsListener;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import android.text.TextUtils;
import android.util.DisplayMetrics;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.widget.LinearLayout;
import android.widget.RelativeLayout;

import static android.app.Activity.RESULT_OK;


public class ForgeViewController {

    public static void onCreate(Bundle savedInstanceState, ViewGroup contentView) {
        // read flags
        ForgeViewController.viewportFit = ViewportFit.AUTO;
        if (ForgeApp.appConfig.has("core") &&
                ForgeApp.appConfig.getAsJsonObject("core").has("android")  &&
                ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("android").has("viewport_fit")) {
            String viewport_fit = ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("android").get("viewport_fit").getAsString();
            if (viewport_fit.equalsIgnoreCase("cover")) {
                ForgeLog.d("Setting viewport_fit=cover");
                ForgeViewController.viewportFit = ViewportFit.COVER;
            }
        }

        // configure viewport_fit behaviour
        Window window = ForgeApp.getActivity().getWindow();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            if (ForgeViewController.viewportFit == ViewportFit.COVER) {
                // enable transparent status bar
                window.clearFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
                window.addFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_STATUS);
                ForgeViewController.statusBarTransparent = true;

                window.getAttributes().layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;

            } else { // viewport-fit=auto
                window.getAttributes().layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_NEVER;
            }
        }

        // Hide UI elements by default
        ForgeViewController.setNavigationBarHidden(true, null);
        ForgeViewController.setTabBarHidden(true, null);

        // WindowInset listener
        ViewCompat.setOnApplyWindowInsetsListener(contentView, new OnApplyWindowInsetsListener() {
            @Override
            public WindowInsetsCompat onApplyWindowInsets(View view, WindowInsetsCompat insets) {
                // update systemWindowInsets
                systemWindowInsets.left = insets.getSystemWindowInsetLeft();
                systemWindowInsets.top = insets.getSystemWindowInsetTop();
                systemWindowInsets.right = insets.getSystemWindowInsetRight();
                systemWindowInsets.bottom = insets.getSystemWindowInsetBottom();

                // update displayCutoutInsets
                DisplayCutoutCompat displayCutout = insets.getDisplayCutout();
                if (displayCutout != null) {
                    displayCutoutInsets.left   = displayCutout.getSafeInsetLeft();
                    displayCutoutInsets.top    = displayCutout.getSafeInsetTop();
                    displayCutoutInsets.right  = displayCutout.getSafeInsetRight();
                    displayCutoutInsets.bottom = displayCutout.getSafeInsetBottom();
                } else {
                    displayCutoutInsets = new RectF(0, 0, 0, 0);
    }

                ForgeLog.d("ForgeViewController::OnApplyWindowInsetsListener -> " +
                        " l:" + displayCutoutInsets.left +
                        " t:" + displayCutoutInsets.top + "(" + systemWindowInsets.top + ")" +
                        " r:" + displayCutoutInsets.right +
                        " b:" + displayCutoutInsets.bottom);

                // force update layout
                ForgeViewController.updateContentInsets(null);

                return insets;
            }
        });
    }


    public static void setStatusBarHidden(final boolean hidden, final Runnable runnable) {
        ForgeViewController.statusBarHidden = hidden;

        ForgeApp.getActivity().runOnUiThread(new Runnable() {
            @Override
            public void run() {
                ForgeActivity activity = ForgeApp.getActivity();

                if (Build.VERSION.SDK_INT < Build.VERSION_CODES.HONEYCOMB_MR2) {
                    if (hidden) {
                        ForgeApp.getActivity().setTheme(android.R.style.Theme);
                    } else {
                        ForgeApp.getActivity().setTheme(android.R.style.Theme_NoTitleBar_Fullscreen);
                    }
                } else if (Build.VERSION.SDK_INT < Build.VERSION_CODES.JELLY_BEAN_MR2) {
                    if (hidden) {
                        ForgeApp.getActivity().setTheme(android.R.style.Theme_Holo_Light_NoActionBar);
                    } else {
                        ForgeApp.getActivity().setTheme(android.R.style.Theme_Holo_Light_NoActionBar_Fullscreen);
                    }
                } else {
                    View decorView = activity.getWindow().getDecorView();
                    int options = decorView.getSystemUiVisibility();
                    if (hidden) {
                        options |= View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN;
                        options |= View.SYSTEM_UI_FLAG_FULLSCREEN;
                    } else {
                        options &= ~View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN;
                        options &= ~View.SYSTEM_UI_FLAG_FULLSCREEN;
                    }
                    decorView.setSystemUiVisibility(options);
                }
                ForgeViewController.updateContentInsets(runnable);
            }
        });
    }


    /**
     * @deprecated Behaviour is now hardcoded:
     *   1. No display cutout shows default opaque statusbar
     *   2. Display cutout shows transparent statusbar
     *   3. Display cutout with navigation bar shows custom opaque statusbar
     * @param transparent
     * @param runnable
     */
    public static void setStatusBarTransparent(final boolean transparent, final Runnable runnable) {
            if (runnable != null) {
                runnable.run();
            }
        /*ForgeApp.getActivity().runOnUiThread(new Runnable() {
            @Override
            public void run() {
                Window window = ForgeApp.getActivity().getWindow();

                if (transparent) {
                    window.clearFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
                    window.addFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_STATUS);
                } else {
                    window.clearFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_STATUS);
                    window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
                }

                ForgeViewController.statusBarTransparent = transparent;
                ForgeViewController.updateContentInsets(runnable);
            }
        });*/
    }


    // TODO document: setStatusBarTransparent needs to be false in order to set colors
    // TODO document: alpha on the status bar color doesn't seem to be supported
    public static void setStatusBarColor(final int color, final Runnable runnable) {
                if (runnable != null) {
                    runnable.run();
                }
        // alpha is not supported it would seem
        ForgeApp.getActivity().runOnUiThread(new Runnable() {
            @Override
            public void run() {
                Window window = ForgeApp.getActivity().getWindow();
                if (Build.VERSION.SDK_INT >= 21) {
                    //ForgeApp.getActivity().getActionBar().setElevation(0);
                    window.getDecorView().setElevation(0);
                    ForgeApp.getActivity().mainLayout.setBackgroundColor(color);
                    window.setStatusBarColor(color);
                } else {
                    ForgeLog.w("display.statusbar.setStatusBarColor() is only supported on Android 5.0 or higher");
                }

                if (runnable != null) {
                    runnable.run();
                }
            }
        });
    }


    // TODO figure out how to get rid of status bar drop shadow :-/
    public static void setNavigationBarHidden(final boolean hidden, final Runnable runnable) {
        ForgeViewController.navigationBarHidden = hidden;

        ForgeApp.getActivity().runOnUiThread(new Runnable() {
            @Override
            public void run() {
                Window window = ForgeApp.getActivity().getWindow();
                if (hidden) {
                    ForgeViewController.navigationBar.setVisibility(View.GONE);
                } else { // no navigation bar with transparent status bar
                    ForgeViewController.navigationBar.setVisibility(View.VISIBLE);
                }
                ForgeViewController.updateContentInsets(runnable);
            }
        });
    }


    public static void setTabBarHidden(final boolean hidden, final Runnable runnable) {
        ForgeViewController.tabBarHidden = hidden;

        ForgeApp.getActivity().runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (hidden) {
                    ForgeViewController.tabBar.setVisibility(View.GONE);
                } else {
                    ForgeViewController.tabBar.setVisibility(View.VISIBLE);
                }
                ForgeViewController.updateContentInsets(runnable);
            }
        });
    }


    /**
     * Return the _actual_ safe area insets because Android only provides cutout or system window inset information separately
     * @return
     */
    public static RectF getSafeAreaInsets() {
        RectF computedInsets = new RectF(displayCutoutInsets.left, displayCutoutInsets.top, displayCutoutInsets.right, displayCutoutInsets.bottom);

        // @hack *sighe* when status bar is transparent, in portrait we use displayCutoutInsets, in landscape it must be systemWindowInset
        //       whoever designed this API clearly never had to use it themselves
        if (ForgeViewController.orientation != Configuration.ORIENTATION_LANDSCAPE &&
            ForgeViewController.statusBarTransparent == true &&
            ForgeViewController.statusBarHidden == false) {
            //computedInsets.top = ForgeConstant.getStatusBarHeightDynamic();
            computedInsets.top = systemWindowInsets.top;
    }

        // @hack move navigation bar below status bar if status bar is visible
        if (ForgeApp.getActivity().navigationBarLayoutParams != null) {
            if (ForgeViewController.orientation == Configuration.ORIENTATION_LANDSCAPE) {
                ForgeApp.getActivity().navigationBarLayoutParams.setMargins(0, 0, 0, 0);
            } else if (ForgeViewController.navigationBarHidden == false) {
                ForgeApp.getActivity().navigationBarLayoutParams.setMargins(0, Math.round(computedInsets.top), 0, 0);
                computedInsets.top = 0;
            }
        }

        // @hack workaround Galaxy S4 / S5 layout bug: https://github.com/trigger-corp/forge/issues/23
        if ((Build.VERSION.SDK_INT == Build.VERSION_CODES.LOLLIPOP ||
                Build.VERSION.SDK_INT == Build.VERSION_CODES.LOLLIPOP_MR1 ||
                Build.VERSION.SDK_INT == Build.VERSION_CODES.M) &&
                Build.MANUFACTURER.equalsIgnoreCase("Samsung")) {
            computedInsets.top += 24;
        }

        ForgeLog.d("ForgeViewController::getSafeAreaInsets -> " +
                " l:" + computedInsets.left +
                " t:" + computedInsets.top +
                " r:" + computedInsets.right +
                " b:" + computedInsets.bottom);

        return computedInsets;
    }


    public static RectF getSafeAreaInsetsPx() {
        DisplayMetrics metrics = new DisplayMetrics();
        ForgeApp.getActivity().getWindowManager().getDefaultDisplay().getMetrics(metrics);

        RectF safeAreaInsetsPx = ForgeViewController.getSafeAreaInsets();
        safeAreaInsetsPx.left   /= metrics.density;
        safeAreaInsetsPx.top    /= metrics.density;
        safeAreaInsetsPx.right  /= metrics.density;
        safeAreaInsetsPx.bottom /= metrics.density;

        return safeAreaInsetsPx;
    }


    public static void onConfigurationChanged(final Configuration configuration, final Runnable runnable) {
        ForgeViewController.orientation = configuration.orientation;

        if (configuration.orientation == Configuration.ORIENTATION_PORTRAIT) {
            ForgeViewController.setStatusBarHidden(statusBarHiddenPortrait, null);

        } else if (configuration.orientation == Configuration.ORIENTATION_LANDSCAPE) {
            ForgeViewController.statusBarHiddenPortrait = ForgeViewController.statusBarHidden;
            ForgeViewController.setStatusBarHidden(true, null);
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT_WATCH) {
            ForgeApp.getActivity().webView.requestApplyInsets();
        }

        if (runnable != null) {
            runnable.run();
        }
    }


    protected static void updateContentInsets(final Runnable runnable) {
        if (ForgeViewController.viewportFit == ViewportFit.AUTO) {
            ForgeLog.d("updateContentInsets viewport_fit=auto");
            if (runnable != null) {
                runnable.run();
            }
            return;
        }

        ForgeLog.d("updateContentInsets viewport_fit=cover");

        RectF computedAreaInsetsPx = ForgeViewController.getSafeAreaInsetsPx();
        float left = computedAreaInsetsPx.left;
        float top = computedAreaInsetsPx.top;
        float right = computedAreaInsetsPx.right;
        float bottom = computedAreaInsetsPx.bottom;

        ForgeWebView webView = ForgeApp.getActivity().webView;
        String update = "var root = document.documentElement;";
        update += "root.style.setProperty('--safe-area-inset-left', '" + left + "px');";
        update += "root.style.setProperty('--safe-area-inset-top', '" + top + "px');";
        update += "root.style.setProperty('--safe-area-inset-right', '" + right + "px');";
        update += "root.style.setProperty('--safe-area-inset-bottom', '" + bottom + "px');";

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
            try {
                webView.evaluateJavascript(update, new ValueCallback<String>() {
                    @Override
                    public void onReceiveValue(String s) {
                        if (runnable != null) {
                            runnable.run();
                        }
                    }
                });
            } catch (Exception e) {
                ForgeLog.e(e.getLocalizedMessage());
                e.printStackTrace();
            }
        } else if (runnable != null) {
            runnable.run();
        }
    }


    /**
     * Handler for WebView file inputs
     * @param webView
     * @param filePathCallback
     * @param fileChooserParams
     * @return
     */
    public static boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, WebChromeClient.FileChooserParams fileChooserParams) {
        ForgeIntentResultHandler resultHandler = new ForgeIntentResultHandler() {
            @Override
            public void result(int requestCode, int resultCode, Intent data) {
                if (resultCode != RESULT_OK) {
                    filePathCallback.onReceiveValue(null);
                    return;
                }

                filePathCallback.onReceiveValue(new Uri[] {
                    data.getData()
                });
            }
        };

        Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        if (Build.VERSION.SDK_INT >= 21)  {
            String[] acceptTypes = fileChooserParams.getAcceptTypes();
            final String[] computedMimeTypes = ForgeUtil.normaliseMimeTypes(TextUtils.join(",", acceptTypes));
            intent.putExtra(Intent.EXTRA_MIME_TYPES, computedMimeTypes);
        } else {
            // Older Android SDK doesn't have a way to specify file type filters
        }

        ForgeApp.intentWithHandler(intent, resultHandler);

        return true;
    }


    public static boolean statusBarHidden;
    public static boolean statusBarHiddenPortrait;
    public static boolean statusBarTransparent;
    public static boolean navigationBarHidden;
    public static boolean tabBarHidden;

    public static RelativeLayout navigationBar = null;
    public static View navigationBarTitle = null;

    public static LinearLayout tabBar;

    public static int orientation = Configuration.ORIENTATION_UNDEFINED;

    private enum ViewportFit {
        AUTO,
        COVER
    }
    private static ViewportFit viewportFit = ViewportFit.AUTO;
    private static RectF displayCutoutInsets = new RectF(0, 0, 0, 0);
    private static RectF systemWindowInsets = new RectF(0, 0, 0, 0);
}
