package io.trigger.forge.android.core;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.res.AssetFileDescriptor;
import android.database.Cursor;
import android.net.Uri;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import com.llamalab.safs.Path;
import com.llamalab.safs.Paths;

import java.io.IOException;
import java.net.URL;

public class ForgeContentProvider extends ContentProvider {

    @Override
    public AssetFileDescriptor openAssetFile(Uri uri, String mode) {
        if (getContext() == null) {
            return null;
        }

        // serve files from package content like:
        //
        //   content://io.trigger.android.forge.ForgeInspector/src/image.jpg
        //
        // primarily used by external intents

        ForgeFile forgeFile = null;

        Path path = Paths.get(uri.getPath());
        if (uri.getPath().startsWith("/forge")) {
            path = Paths.get("/forge").relativize(path);
            forgeFile = new ForgeFile(ForgeStorage.EndpointId.Forge, path.toString());

        } else if (uri.getPath().startsWith("/src")) {
            path = Paths.get("/src").relativize(path);
            forgeFile = new ForgeFile(ForgeStorage.EndpointId.Source, path.toString());

        } else {
            ForgeLog.e("ForgeContentProvider failed to locate file descriptor for uri: " + uri.toString());
            return null;
        }

        try {
            return ForgeStorage.getFileDescriptor(forgeFile);
        } catch (IOException e) {
            ForgeLog.e("ForgeContentProvider failed to obtain file descriptor for uri: " +
                    uri.toString() + " " + e.getLocalizedMessage());
        }

        return null;
    }

    //region ContentProvider

    @Override
    public boolean onCreate() {
        return false;
    }

    @Nullable
    @Override
    public Cursor query(@NonNull Uri uri, @Nullable String[] strings, @Nullable String s, @Nullable String[] strings1, @Nullable String s1) {
        return null;
    }

    @Nullable
    @Override
    public String getType(@NonNull Uri uri) {
        return null;
    }

    @Nullable
    @Override
    public Uri insert(@NonNull Uri uri, @Nullable ContentValues contentValues) {
        return null;
    }

    @Override
    public int delete(@NonNull Uri uri, @Nullable String s, @Nullable String[] strings) {
        return 0;
    }

    @Override
    public int update(@NonNull Uri uri, @Nullable ContentValues contentValues, @Nullable String s, @Nullable String[] strings) {
        return 0;
    }

    //endregion ContentProvider
}
