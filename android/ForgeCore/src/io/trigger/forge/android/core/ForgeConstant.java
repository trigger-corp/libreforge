package io.trigger.forge.android.core;

import android.content.res.Resources;
import android.graphics.Rect;
import android.os.Build;
import android.util.DisplayMetrics;
import android.view.Window;

public class ForgeConstant {
    public static float getStatusBarHeightDynamic() {
        int statusBarHeight = 0;

        final Resources resources = ForgeApp.getActivity().getResources();
        int resourceId = resources.getIdentifier("status_bar_height", "dimen", "android");
        if (resourceId > 0) {
            statusBarHeight = resources.getDimensionPixelSize(resourceId);
        } else {
            statusBarHeight = (int) Math.ceil((Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? 24 : 25) * resources.getDisplayMetrics().density);
        }

        ForgeLog.i("ForgeConstant.getStatusBarHeightDynamic -> " + statusBarHeight);
        return statusBarHeight;
    }


    public static float getStatusBarHeightDynamicPx() {
        float statusBarHeightPx = ForgeConstant.getStatusBarHeightDynamic() / ForgeConstant.getDensity();
        ForgeLog.i("ForgeConstant.getStatusBarHeightDynamicPx -> " + statusBarHeightPx);
        return statusBarHeightPx;
    }


    public static float getNavigationBarHeightStatic() {
        return ForgeConstant.getNavigationBarHeightStaticPx() * ForgeConstant.getDensity();
    }

    private static float getNavigationBarHeightStaticPx() {
        return 50;
    }


    public static float getNavigationBarTextHeightStatic() {
        return ForgeConstant.getNavigationBarTextHeightStaticPx() * ForgeConstant.getDensity();
    }


    private static float getNavigationBarTextHeightStaticPx() {
        return 24;
    }


    public static float getTabBarSizeStatic() {
        return ForgeConstant.getTabBarSizeStaticPx() * ForgeConstant.getDensity();
    }


    private static float getTabBarSizeStaticPx() {
        return 75;
    }


    private static float getDensity() {
        DisplayMetrics metrics = new DisplayMetrics();
        ForgeApp.getActivity().getWindowManager().getDefaultDisplay().getMetrics(metrics);
        return metrics.density;
    }

}
