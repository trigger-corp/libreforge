package io.trigger.forge.android.modules.layout;

import android.graphics.Color;
import android.graphics.RectF;

import android.util.DisplayMetrics;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

import io.trigger.forge.android.core.ForgeApp;
import io.trigger.forge.android.core.ForgeLog;
import io.trigger.forge.android.core.ForgeParam;
import io.trigger.forge.android.core.ForgeTask;
import io.trigger.forge.android.core.ForgeViewController;

public class API {

    public static void setStatusBarHidden(final ForgeTask task, @ForgeParam("hidden") final boolean hidden) {
        ForgeViewController.setStatusBarHidden(hidden, new Runnable() {
            @Override
            public void run() {
                task.success();
            }
        });
    }


    public static void setStatusBarTransparent(final ForgeTask task, @ForgeParam("transparent") final boolean transparent) {
        ForgeViewController.setStatusBarTransparent(transparent, new Runnable() {
            @Override
            public void run() {
                task.success();
            }
        });
    }


    public static void setStatusBarColor(final ForgeTask task, @ForgeParam("color") final JsonArray colorArray) {
        int color;
        if (colorArray.size() == 4) {
            color = Color.argb(colorArray.get(3).getAsInt(), colorArray.get(0).getAsInt(), colorArray.get(1).getAsInt(), colorArray.get(2).getAsInt());
        } else if (colorArray.size() == 3) {
            color = Color.rgb(colorArray.get(0).getAsInt(), colorArray.get(1).getAsInt(), colorArray.get(2).getAsInt());
        } else {
            task.error("invalid color array, expecting: [r, g, b] or [r, g, b, a]");
            return;
        }
        ForgeViewController.setStatusBarColor(color, new Runnable() {
            @Override
            public void run() {
                task.success();
            }
        });
    }


    public static void setStatusBarStyle(final ForgeTask task, @ForgeParam("style") final String style) {
        ForgeLog.d("setStatusBarStyle is not supported on Android");
        task.success();
    }


    public static void setNavigationBarHidden(final ForgeTask task, @ForgeParam("hidden") final boolean hidden) {
        ForgeViewController.setNavigationBarHidden(hidden, new Runnable() {
            @Override
            public void run() {
                task.success();
            }
        });
    }


    public static void setTabBarHidden(final ForgeTask task, @ForgeParam("hidden") final boolean hidden) {
        ForgeViewController.setTabBarHidden(hidden, new Runnable() {
            @Override
            public void run() {
                task.success();
            }
        });
    }


    public static void getSafeAreaInsets(final ForgeTask task) {
        ForgeApp.getActivity().runOnUiThread(new Runnable() {
            @Override
            public void run() {
                RectF rect = ForgeViewController.getSafeAreaInsetsPx();
                JsonObject safeAreaInsets = new JsonObject();
                safeAreaInsets.addProperty("left",   rect.left);
                safeAreaInsets.addProperty("top",    rect.top);
                safeAreaInsets.addProperty("right",  rect.right);
                safeAreaInsets.addProperty("bottom", rect.bottom);
                task.success(safeAreaInsets);
            }
        });
    }
}
