package io.trigger.forge.android.core;

import java.io.DataInputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TimeZone;

import android.content.res.AssetFileDescriptor;
import android.database.Cursor;
import android.net.Uri;
import android.provider.MediaStore;
import android.webkit.MimeTypeMap;

import com.google.gson.JsonObject;
import com.llamalab.safs.Path;
import com.llamalab.safs.Paths;

import io.trigger.forge.android.core.ForgeStorage.EndpointId;


/**
 * Object containing information about a file with methods to access it.
 */
public class ForgeFile {
    private EndpointId endpointId;
    private Path resource;


    //region Lifecycle

    /**
     * Construct a ForgeFile from the given endpointId and resource path
     * @param endpointId
     * @param resource
     */
    public ForgeFile(EndpointId endpointId, Path resource) {
        this.endpointId = endpointId;
        this.resource = resource;
    }

    /**
     * Construct a ForgeFile from the given endpointId and resource string
     * @param endpointId
     * @param resource
     */
    public ForgeFile(EndpointId endpointId, String resource) {
        this.endpointId = endpointId;
        this.resource = Paths.get(resource);
    }

    /**
     * Construct a ForgeFile from a Javascript File object
     * @param scriptObject JSON file object, must contain an `endpoint` and a `resource` property
     */
    public ForgeFile(JsonObject scriptObject) {
        if (!scriptObject.has("endpoint")) {
            throw new IllegalArgumentException("File object requires property: endpoint");
        } else if (!scriptObject.has("resource")) {
            throw new IllegalArgumentException("File object requires property: resource");
        }
        this.endpointId = ForgeStorage.idForEndpoint(scriptObject.get("endpoint").getAsString());
        this.resource = Paths.get(scriptObject.get("resource").getAsString());
    }

    //endregion Lifecycle


    //region Helpers

    /**
     * @return A JSON representation of this file object suitable for use by Forge javascript API's
     */
    public JsonObject toScriptObject() {
        JsonObject scriptObject = new JsonObject();
        scriptObject.addProperty("endpoint", this.getEndpoint());
        scriptObject.addProperty("resource", this.resource.toString());

        return scriptObject;
    }

    public String toString() {
        return this.toScriptObject().toString();
    }

    //endregion Helpers


    //region Properties

    public String getEndpoint() {
        return ForgeStorage.endpointForId(this.endpointId);
    }

    public EndpointId getEndpointId() {
        return this.endpointId;
    }

    public Path getResource() {
        return this.resource;
    }

    /**
     * Access the files mime-type (if available)
     * @return the files mime-type
     */
    public String getMimeType() {
        String fileName = this.resource.getFileName().toString();
        String extension = MimeTypeMap.getFileExtensionFromUrl(fileName);
        if (extension == null) {
            // TODO check header bytes
            return "application/octet-stream";
        }

        // check extension against MimeTypeMap
        String mimeType = MimeTypeMap.getSingleton().getMimeTypeFromExtension(extension);
        if (mimeType != null) {
            return mimeType;
        }

        // check for extensions that MimeTypeMap does not know about
        mimeType = this.getMimeTypeFromExtension(extension);
        if (mimeType != null) {
            return mimeType;
        }

        // TODO check header bytes
        return "application/octet-stream";
    }

    //endregion Properties


    //region Interface

    /**
     * @return Whether the file referenced by this object exists
     */
    public boolean exists() {
        try {
            return ForgeStorage.getFileDescriptor(this) != null;
        } catch (IOException e) {
            return false;
        }
    }

    /**
     * Returns file information
     * @return {size, date, mimetype}
     */
    public JsonObject getAttributes() throws IOException {
        // get file modification time
        long added = 0;
        long modified = 0;

        if (this.endpointId == EndpointId.Forge) {
            added = BuildConfig.TIMESTAMP;
            modified = BuildConfig.TIMESTAMP;

        } else if (this.endpointId == EndpointId.Source) {
            // TODO check if we have a reloaded version of this file
            added = BuildConfig.TIMESTAMP;
            modified = BuildConfig.TIMESTAMP;

        } else {
            URL url = ForgeStorage.getNativeURL(this);
            Path path = Paths.get(url.getFile());
            File file = path.toFile();
            added = file.lastModified();
            modified = file.lastModified();
        }

        // get file size
        AssetFileDescriptor fileDescriptor = ForgeStorage.getFileDescriptor(this);
        long fileSize = fileDescriptor.getLength();

        // date formatter
        SimpleDateFormat df = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'");
        df.setTimeZone(TimeZone.getTimeZone("UTC"));

        // build response
        JsonObject attributes = new JsonObject();
        attributes.addProperty("size", fileSize);
        attributes.addProperty("added", df.format(new Date(added)));
        attributes.addProperty("modified", df.format(new Date(modified)));
        attributes.addProperty("mimetype", this.getMimeType());

        attributes.addProperty("date", df.format(new Date(modified))); // deprecated

        return attributes;
    }

    /**
     * Access the files contents
     * @return The bytes contained in the referenced file
     * @throws IOException
     */
    public byte[] getContents() throws IOException  {
        // TODO support width/height?
        AssetFileDescriptor fileDescriptor = ForgeStorage.getFileDescriptor(this);
        InputStream inputStream = new DataInputStream(fileDescriptor.createInputStream());
        byte[] bytes = new byte[inputStream.available()];
        inputStream.read(bytes, 0, inputStream.available());
        if (inputStream != null) {
            try {
                inputStream.close();
            } catch (IOException e) { }
        }
        return bytes;
    }


    /**
     * Delete the file (if possible)
     * @return Whether or not the file was deleted
     */
    public boolean remove() throws IOException {
        final List<EndpointId> mutableEndpoints = Arrays.asList(
            EndpointId.Temporary,
            EndpointId.Permanent,
            EndpointId.Documents
        );
        if (!mutableEndpoints.contains(this.endpointId)) {
            throw new IOException("Cannot remove file from protected endpoint: " + this.getEndpoint());
        }

        File file = new File(ForgeStorage.getNativeURL(this).getPath());

        return file.delete();
    }

    //endregion Interface


    //region Private Helpers

    /**
     * @hide
     *
     * Fallback implementation of getMimeType
     */
    @SuppressWarnings("serial")
    private static final Map<String, String> MIME_TYPES = new HashMap<String, String>() {
        {
            put("css", "text/css");
            put("htm", "text/html");
            put("html", "text/html");
            put("xml", "text/xml");
            put("java", "text/x-java-source, text/java");
            put("md", "text/plain");
            put("txt", "text/plain");
            put("asc", "text/plain");
            put("gif", "image/gif");
            put("jpg", "image/jpeg");
            put("jpeg", "image/jpeg");
            put("png", "image/png");
            put("svg", "image/svg+xml");
            put("mp3", "audio/mpeg");
            put("m3u", "audio/mpeg-url");
            put("mp4", "video/mp4");
            put("ogv", "video/ogg");
            put("flv", "video/x-flv");
            put("mov", "video/quicktime");
            put("swf", "application/x-shockwave-flash");
            put("js", "application/javascript");
            put("pdf", "application/pdf");
            put("doc", "application/msword");
            put("ogg", "application/x-ogg");
            put("zip", "application/octet-stream");
            put("exe", "application/octet-stream");
            put("class", "application/octet-stream");
            put("m3u8", "application/vnd.apple.mpegurl");
            put("ts", " video/mp2t");
        }
    };
    private String getMimeTypeFromExtension(String extension) {
        return ForgeFile.MIME_TYPES.get(extension.toLowerCase());
    }

    //endregion Private Helpers
}
