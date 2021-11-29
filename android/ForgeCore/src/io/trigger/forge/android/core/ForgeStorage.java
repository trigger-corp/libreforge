package io.trigger.forge.android.core;

import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.res.AssetFileDescriptor;
import android.os.Environment;
import android.os.ParcelFileDescriptor;

import com.google.common.base.Charsets;
import com.google.common.io.Files;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.llamalab.safs.Path;
import com.llamalab.safs.Paths;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;
import java.util.Stack;
import java.util.UUID;

import io.trigger.forge.android.modules.httpd.EventListener;


public class ForgeStorage {

    //region Types

    public static class Endpoints {
        public static final String Forge = "/forge";
        public static final String Source = "/src";
        public static final String Temporary = "/temporary";
        public static final String Permanent = "/permanent";
        public static final String Documents = "/documents";
    }

    public enum EndpointId {
        Forge(1),
        Source(2),
        Temporary(3),
        Permanent(4),
        Documents(5);

        private int value;
        private static Map map = new HashMap<>();

        private EndpointId(int value) {
            this.value = value;
        }

        static {
            for (EndpointId endpointId : EndpointId.values()) {
                map.put(endpointId.value, endpointId);
            }
        }

        public static EndpointId valueOf(int endpointId) {
            return (EndpointId) map.get(endpointId);
        }

        public int getValue() {
            return value;
        }
    }

    public static class Directories {
        public static URL Forge() {
            String packageName = ForgeApp.getActivity().getApplicationContext().getPackageName();
            URL url = null;
            try {
                // TODO technically this should be content:// but that requires wholesale replacement of URL
                //      with Uri in the codebase. This may still be worth doing.
                url = new URL("file:///" + packageName + "/forge");
            } catch (MalformedURLException e) {
                e.printStackTrace();
            }
            return url;
        }

        public static URL Source() {
            String packageName = ForgeApp.getActivity().getApplicationContext().getPackageName();
            URL url = null;
            try {
                // TODO technically this should be content:// but that requires wholesale replacement of URL
                //      with Uri in the codebase. This may still be worth doing.
                url = new URL("file:///" + packageName + "/src");
            } catch (MalformedURLException e) {
                e.printStackTrace();
            }
            return url;
        }

        public static URL Temporary() {
            // <cache-path name="name" path="path" />
            Path cacheDirectory = Paths.get(ForgeApp.getActivity().getCacheDir().getPath(), "forgecore");
            File directory = cacheDirectory.toFile();
            if (!directory.exists()) {
                directory.mkdirs();
            }
            URL url = null;
            try {
                url = directory.toURI().toURL();
            } catch (MalformedURLException e) {
                e.printStackTrace();
            }
            return url;
        }

        public static URL Permanent() {
            // <files-path name="name" path="path" />
            File directory = ForgeApp.getActivity().getDir("forgecore", Context.MODE_PRIVATE);
            URL url = null;
            try {
                url = directory.toURI().toURL();
            } catch (MalformedURLException e) {
                e.printStackTrace();
            }
            return url;
        }

        public static URL Documents() {
            // <external-files-path name="name" path="path" />
            File directory = null;
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.KITKAT) {
                directory = ForgeApp.getActivity().getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS);
            } else {
                directory = ForgeApp.getActivity().getExternalFilesDir(null);
            }
            URL url = null;
            try {
                url = directory.toURI().toURL();
            } catch (MalformedURLException e) {
                e.printStackTrace();
            }
            return url;
        }
    }

    //endregion Types


    //region Lookups

    public static String endpointForId(EndpointId endpointId) throws IllegalArgumentException {
        switch (endpointId) {
            case Forge:
                return Endpoints.Forge;
            case Source:
                return Endpoints.Source;
            case Temporary:
                return Endpoints.Temporary;
            case Permanent:
                return Endpoints.Permanent;
            case Documents:
                return Endpoints.Documents;
        }
        throw new IllegalArgumentException("Invalid endpoint id: " + endpointId);
    }

    public static EndpointId idForEndpoint(String endpoint) throws IllegalArgumentException {
        if (endpoint.equalsIgnoreCase(Endpoints.Forge)) {
            return EndpointId.Forge;
        } else if (endpoint.equalsIgnoreCase(Endpoints.Source)) {
            return EndpointId.Source;
        } else if (endpoint.equalsIgnoreCase(Endpoints.Temporary)) {
            return EndpointId.Temporary;
        } else if (endpoint.equalsIgnoreCase(Endpoints.Permanent)) {
            return EndpointId.Permanent;
        } else if (endpoint.equalsIgnoreCase(Endpoints.Documents)) {
            return EndpointId.Documents;
        }
        throw new IllegalArgumentException("Invalid endpoint: " + endpoint);
    }

    //endregion Lookups


    //region Interface

    /**
     * returns a URL for the file which is suitable for use by native Android API's
     * @param file
     * @return
     */
    public static URL getNativeURL(ForgeFile file) {
        URL url = null;

        EndpointId endpointId = file.getEndpointId();
        if (endpointId == EndpointId.Forge) {
            url = ForgeStorage.Directories.Forge();
        } else if (endpointId == EndpointId.Source) {
            url = ForgeStorage.Directories.Source();
        } else if (endpointId == EndpointId.Temporary) {
            url = ForgeStorage.Directories.Temporary();
        } else if (endpointId == EndpointId.Permanent) {
            url = ForgeStorage.Directories.Permanent();
        } else if (endpointId == EndpointId.Documents) {
            url = ForgeStorage.Directories.Documents();
        } else {
            throw new IllegalArgumentException("Invalid endpoint for file: " + file);
        }

        // construct from individual components to make sure we return a nice clean url
        Path path = Paths.get(url.getPath(), file.getResource().toAbsolutePath().toString());
        try {
            url = new URL(url.getProtocol(), url.getHost(), url.getPort(), path.toString());
        } catch (MalformedURLException e) {
            ForgeLog.e("ForgeStorage.getNativeURL could not construct a native url for file: " + file.toString());
            e.printStackTrace();
        }

        return url;
    }

    /**
     * returns a URL for the file which is suitable for consumption by the Embedded Server / WebView
     * @param file
     * @return
     */
    public static URL getScriptURL(ForgeFile file) {
        URL httpd = EventListener.getURL();
        Path scriptPath = ForgeStorage.getScriptPath(file);
        URL scriptURL = null;
        try {
            scriptURL = new URL(httpd.getProtocol(), httpd.getHost(), httpd.getPort(), scriptPath.toString());
        } catch (MalformedURLException e) {
            ForgeLog.e("ForgeStorage.getScriptURL could not construct a script url for file: " + file.toString());
            e.printStackTrace();
        }
        return scriptURL;
    }

    /**
     * returns a path for the file which is suitable for consumption by the Embedded Server / WebView
     * @param file
     * @return
     */
    public static Path getScriptPath(ForgeFile file) {
        Path scriptPath = Paths.get(file.getEndpoint(), file.getResource().toString());
        return scriptPath.toAbsolutePath();
    }

    /**
     * return an AssetFileDescriptor for the given file
     * @return
     */
    public static AssetFileDescriptor getFileDescriptor(ForgeFile forgeFile) throws IOException {
        EndpointId endpointId = forgeFile.getEndpointId();

        if (endpointId == EndpointId.Forge) {
            return ForgeStorage.getFileDescriptorForAppAsset(forgeFile);

        } else if (endpointId == EndpointId.Source) {
            AssetFileDescriptor fileDescriptor = ForgeStorage.getFileDescriptorForReloadableAsset(forgeFile);
            if (fileDescriptor != null) {
                return fileDescriptor;
            }
            return ForgeStorage.getFileDescriptorForAppAsset(forgeFile);

        } else if (endpointId == EndpointId.Temporary) {
            URL url = ForgeStorage.getNativeURL(forgeFile);
            File file = new File(url.getFile());
            ParcelFileDescriptor fileDescriptor = ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY);
            return new AssetFileDescriptor(fileDescriptor, 0, AssetFileDescriptor.UNKNOWN_LENGTH);

        } else if (endpointId == EndpointId.Permanent) {
            URL url = ForgeStorage.getNativeURL(forgeFile);
            File file = new File(url.getFile());
            ParcelFileDescriptor fileDescriptor = ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY);
            return new AssetFileDescriptor(fileDescriptor, 0, AssetFileDescriptor.UNKNOWN_LENGTH);

        } else if (endpointId == EndpointId.Documents) {
            URL url = ForgeStorage.getNativeURL(forgeFile);
            File file = new File(url.getFile());
            ParcelFileDescriptor fileDescriptor = ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY);
            return new AssetFileDescriptor(fileDescriptor, 0, AssetFileDescriptor.UNKNOWN_LENGTH);
        }

        throw new IOException("Unsupported endpointId: " + endpointId);
    }

    /**
     * returns storage size information for the device, app and its endpoints
     * @return
     */
    public static JsonObject getSizeInformation() throws IOException {
        PackageInfo packageInfo = null;
        try {
            packageInfo = ForgeApp.getActivity().getPackageManager().getPackageInfo(ForgeApp.getActivity().getPackageName(), 0);
        } catch (PackageManager.NameNotFoundException e) {
            throw new IOException(e.getLocalizedMessage());
        }

        File applicationDirectory = new File(packageInfo.applicationInfo.dataDir);
        File cacheDirectory = ForgeApp.getActivity().getCacheDir();
        File temporaryDirectory = Paths.get(ForgeStorage.Directories.Temporary().getPath()).toFile();
        File permanentDirectory = Paths.get(ForgeStorage.Directories.Permanent().getPath()).toFile();
        File documentsDirectory = Paths.get(ForgeStorage.Directories.Documents().getPath()).toFile();

        long totalSize = applicationDirectory.getTotalSpace();
        long freeSize = applicationDirectory.getUsableSpace();
        long appSize = ForgeStorage.getDirectorySize(applicationDirectory);
        long forgeSize = ForgeStorage.getAssetFolderSize(ForgeStorage.EndpointId.Forge);
        long sourceSize = ForgeStorage.getAssetFolderSize(ForgeStorage.EndpointId.Source); // TODO check for reload
        long cacheSize = ForgeStorage.getDirectorySize(cacheDirectory);
        long temporarySize = ForgeStorage.getDirectorySize(temporaryDirectory);
        long permanentSize = ForgeStorage.getDirectorySize(permanentDirectory);
        long documentsSize = ForgeStorage.getDirectorySize(documentsDirectory);

        JsonObject result = new JsonObject();
        result.addProperty("total", totalSize);
        result.addProperty("free",  freeSize);
        result.addProperty("app",   appSize);

        JsonObject endpoints = new JsonObject();
        endpoints.addProperty("forge", forgeSize);
        endpoints.addProperty("source", sourceSize);
        endpoints.addProperty("temporary", temporarySize);
        endpoints.addProperty("permanent", permanentSize);
        endpoints.addProperty("documents", documentsSize);
        result.add("endpoints", endpoints);

        result.addProperty("cache", cacheSize); // deprecated

        return result;
    }

    /**
     * Generate a temporary file name with the given extension
     * @param extension
     * @return
     */
    public static String temporaryFileNameWithExtension(String extension) {
        String uuid = UUID.randomUUID().toString();
        return uuid + "." + extension;
    }

    //endregion Interface


    //region Helpers

    /**
     * @hide
     * @return null if a reload asset could not be located and needs to be obtained from the original asset directory instead
     */
    protected static AssetFileDescriptor getFileDescriptorForReloadableAsset(ForgeFile forgeFile) throws IOException {
        Context context = ForgeApp.getActivity();

        // only files in the src/ directory can be reloaded
        if (forgeFile.getEndpointId() != EndpointId.Source) {
            return null;
        }

        // check if we have reload content available
        File reloadDirectory = context.getDir("reload-live", Context.MODE_PRIVATE);
        File manifestFile = new File(reloadDirectory, "manifest");
        if (!manifestFile.exists()) {
            return null;
        }

        // get relative path for asset
        String packageName = ForgeApp.getActivity().getApplicationContext().getPackageName();
        URL url = ForgeStorage.getNativeURL(forgeFile);
        Path path = Paths.get(url.getFile());
        path = Paths.get("/" + packageName + "/src").relativize(path);

        // look for file in reload manifest
        JsonObject manifest = new JsonParser().parse(Files.toString(manifestFile, Charsets.UTF_8)).getAsJsonObject();
        if (!manifest.has(path.toString())) {
            ForgeLog.w("Reload manifest has no entry for asset: " + path.toString());
            return null;
        }

        URL assetURL = new URL(manifest.get(path.toString()).getAsString());
        String assetHash = Paths.get(assetURL.getFile()).getFileName().toString();
        File assetFile = new File(reloadDirectory, assetHash);
        if (!assetFile.exists()) {
            ForgeLog.w("Reload directory has no file for asset: " + path.toString() + " with hash: " + assetHash);
            return null;
        }

        return new AssetFileDescriptor(ParcelFileDescriptor.open(assetFile, ParcelFileDescriptor.MODE_READ_ONLY),
                0, AssetFileDescriptor.UNKNOWN_LENGTH);
    }

    /**
     * @hide
     */
    protected static AssetFileDescriptor getFileDescriptorForAppAsset(ForgeFile forgeFile) throws IOException {
        // get relative path for asset
        String packageName = ForgeApp.getActivity().getApplicationContext().getPackageName();
        URL url = ForgeStorage.getNativeURL(forgeFile);
        Path path = Paths.get(url.getFile());
        path = Paths.get("/" + packageName).relativize(path);

        try {
            return ForgeApp.getActivity().getAssets().openFd(path.toString());
        } catch (FileNotFoundException e) {
            return ForgeStorage.getFileDescriptorForCompressedAsset(path);
        }
    }

    /**
     * @hide
     * For reasons unknown assets are compressed when debugging inside AndroidStudio
     */
    private static AssetFileDescriptor getFileDescriptorForCompressedAsset(Path path) throws IOException {
        Context context = ForgeApp.getActivity();
        final File temporaryFile = File.createTempFile("temp", path.getFileName().toString(),
                context.getCacheDir());

        FileOutputStream outputStream = null;
        try {
            outputStream = new FileOutputStream(temporaryFile);
        } catch (FileNotFoundException e2) {
            return null;
        }

        int read;
        byte[] buffer = new byte[1024];
        InputStream inputStream = context.getAssets().open(path.toString());

        while ((read = inputStream.read(buffer)) != -1) {
            outputStream.write(buffer, 0, read);
        }

        inputStream.close();
        outputStream.close();

        return new AssetFileDescriptor(ForgeStorage.autoDeleteFile(temporaryFile), 0, AssetFileDescriptor.UNKNOWN_LENGTH);
    }

    /**
     * @hide
     */
    protected static ParcelFileDescriptor autoDeleteFile(final File file) {
        try {
            return new ParcelFileDescriptor(ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY)) {
                @Override
                public void close() throws IOException {
                    super.close();
                    file.delete();
                };
            };
        } catch (FileNotFoundException e) {
            return null;
        }
    }

    private static long getDirectorySize(File directory) {
        long totalSize = 0;

        Stack<File> directories = new Stack<File>();
        directories.clear();
        directories.push(directory);

        while (!directories.isEmpty()) {
            File current = directories.pop();
            File[] files = current.listFiles();

            for (File file: files){
                if (file.isDirectory()) {
                    directories.push(file);
                } else {
                    totalSize += file.length();
                }
            }
        }

        return totalSize;
    }

    private static long getAssetFolderSize(ForgeStorage.EndpointId endpointId) throws IOException {
        long totalSize = 0;
        Stack<String> directories = new Stack<String>();
        directories.clear();

        Path root = Paths.get("/").relativize(Paths.get(ForgeStorage.endpointForId(endpointId)));
        directories.push(root.toString());

        while (!directories.isEmpty()) {
            String current = directories.pop();
            String[] files = ForgeApp.getActivity().getAssets().list(current);

            for (String file : files) {
                file = current + "/" + file;
                String[] isDirectoryList = ForgeApp.getActivity().getAssets().list(file);
                if (isDirectoryList.length > 0) { // isDirectory
                    directories.push(file);
                } else {
                    file = file.replaceFirst(root.toString(), ""); // strip endpoint
                    ForgeFile forgeFile = new ForgeFile(endpointId, file);
                    try {
                        totalSize += ForgeStorage.getFileDescriptor(forgeFile).getLength();
                    } catch (FileNotFoundException e) {} // isEmptyDirectory
                }
            }
        }

        return totalSize;
    }

    //endregion Helpers

}
