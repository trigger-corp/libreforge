package io.trigger.forge.android.modules.tools;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.net.Uri;

import java.util.List;

import io.trigger.forge.android.core.ForgeActivity;
import io.trigger.forge.android.core.ForgeApp;
import io.trigger.forge.android.core.ForgeFile;
import io.trigger.forge.android.core.ForgeParam;
import io.trigger.forge.android.core.ForgeStorage;
import io.trigger.forge.android.core.ForgeTask;

public class API {
    // used to be called getLocal
    public static void getFileFromSourceDirectory(final ForgeTask task, @ForgeParam("resource") final String resource) {
        // TODO check if we still need this
        ForgeApp.getActivity().requestPermission(Manifest.permission.READ_EXTERNAL_STORAGE, new ForgeActivity.EventAccessBlock() {
            @Override
            public void run(boolean granted) {
                if (!granted) {
                    task.error("Permission denied. User didn't grant access to storage.", "EXPECTED_FAILURE", null);
                    return;
                }
                ForgeFile forgeFile = new ForgeFile(ForgeStorage.EndpointId.Source, resource);
                task.success(forgeFile.toScriptObject());
            }
        });
    }

    // used to be called getURL
    public static void getURLFromSourceDirectory(final ForgeTask task, @ForgeParam("resource") final String resource) {
        try {
            if (resource.startsWith("http:") || resource.startsWith("https:")) {
                task.success(resource);
            } else {
                ForgeFile forgeFile = new ForgeFile(ForgeStorage.EndpointId.Source, resource);
                task.success(ForgeStorage.getScriptURL(forgeFile).toString());
            }
        } catch (Exception e) {
            task.error(e);
        }
    }

    public static void openInWebView(final ForgeTask task, @ForgeParam("url") final String url) {
        Uri uri = null;
        try {
            uri = Uri.parse(url);
        } catch (Exception e) {
            task.error(e);
            return;
        }
        if (uri == null) {
            task.error("Invalid url");
            return;
        }
        task.success();
        ForgeApp.getActivity().gotoUrl(url);
    }

    public static void openWithDevice(final ForgeTask task, @ForgeParam("url") final String url) {
        Uri uri = null;
        try {
            uri = Uri.parse(url);
        } catch (Exception e) {
            task.error(e);
            return;
        }
        if (uri == null) {
            task.error("Invalid url");
            return;
        }

        Intent intent = new Intent(Intent.ACTION_VIEW, uri);
        intent.addCategory(Intent.CATEGORY_BROWSABLE);
        final PackageManager packageManager = ForgeApp.getActivity().getPackageManager();
        List<ResolveInfo> list = packageManager.queryIntentActivities(intent, 0);
        if (list.size() > 0) {
            task.success();
            ForgeApp.getActivity().startActivity(intent);     // Intent exists, invoke it.
        } else {
            // device doesn't know what to do with the URL
            task.error("Device does not know how to handle url");
        }
    }
}
