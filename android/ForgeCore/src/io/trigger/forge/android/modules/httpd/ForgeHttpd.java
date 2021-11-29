package io.trigger.forge.android.modules.httpd;

import io.trigger.forge.android.core.ForgeFile;
import io.trigger.forge.android.core.ForgeLog;

import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.URISyntaxException;

import com.google.gson.JsonObject;
import com.llamalab.safs.Path;
import com.llamalab.safs.Paths;

import android.content.res.AssetFileDescriptor;

import io.trigger.forge.android.core.ForgeStorage;
import io.trigger.forge.android.modules.httpd.fi_iki_elonen.NanoHTTPD;

public class ForgeHttpd extends NanoHTTPD {
    /**
     * Construction
     */
    public ForgeHttpd(String host, int port) {
        super(host, port);
    }

    protected Response FORBIDDEN(String s) {
        return newFixedLengthResponse(Response.Status.FORBIDDEN, NanoHTTPD.MIME_PLAINTEXT, "FORBIDDEN: " + s);
    }

    protected Response INTERNAL_ERROR(String s) {
        return newFixedLengthResponse(Response.Status.INTERNAL_ERROR, NanoHTTPD.MIME_PLAINTEXT, "INTERNAL ERROR: " + s);
    }

    protected Response NOT_FOUND() {
        return newFixedLengthResponse(Response.Status.NOT_FOUND, NanoHTTPD.MIME_PLAINTEXT, "Error 404, file not found.");
    }


    @Override
    public Response serve(IHTTPSession session) {
        URI uri = null;
        try {
            uri = (new URI(session.getUri())).normalize();
        } catch (URISyntaxException e) {
            return newFixedLengthResponse(Response.Status.INTERNAL_ERROR, "text/plain", "INTERNAL ERROR Couldn't parse URL '" + session.getUri() + "': " + e);
        }

        // Handle /favicon.ico and other invalid requests
        Path path = Paths.get(uri.getPath());
        if (path.startsWith("/favicon.ico")) {
            return NOT_FOUND();
        } else if (path.getNameCount() < 2) {
            ForgeLog.w("404 Not found: " + path);
            return NOT_FOUND();
        }

        // Parse request
        ForgeStorage.EndpointId endpointId = null;
        Path resource = null;
        try {
            String endpoint = path.subpath(0, 1).toAbsolutePath().toString();
            endpointId = ForgeStorage.idForEndpoint(endpoint);
            resource = path.subpath(1, path.getNameCount()).toAbsolutePath();
        } catch (IllegalArgumentException e) {
            String message = "Unsupported endpoint or resource: " + path.toString();
            ForgeLog.e(message);
            return INTERNAL_ERROR(message);
        }

        // Obtain file descriptor
        ForgeFile forgeFile = new ForgeFile(endpointId, resource);
        AssetFileDescriptor fileDescriptor = null;
        try {
            fileDescriptor = ForgeStorage.getFileDescriptor(forgeFile);
        } catch (IOException e) {
            e.printStackTrace();
            ForgeLog.w("404 Not found: " + path + " - " + e.getLocalizedMessage());
            return NOT_FOUND();
        }

        // Open stream for reading
        InputStream inputStream;
        try {
            inputStream = fileDescriptor.createInputStream();
        } catch (IOException e) {
            String message = "Couldn't open input stream for resource '" + path + "': " + e.getLocalizedMessage();
            ForgeLog.w(message);
            return INTERNAL_ERROR(message);
        }

        // Serve response
        String mimeType = forgeFile.getMimeType();
        return newChunkedResponse(Response.Status.OK, mimeType, inputStream);
    }

}
