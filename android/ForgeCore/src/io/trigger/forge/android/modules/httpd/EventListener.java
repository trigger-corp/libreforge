package io.trigger.forge.android.modules.httpd;

import android.content.Context;
import android.content.res.AssetFileDescriptor;

import com.google.gson.JsonObject;

import io.trigger.forge.android.core.ForgeStorage;
import io.trigger.forge.android.core.R;
import io.trigger.forge.android.modules.httpd.fi_iki_elonen.NanoHTTPD;
import io.trigger.forge.android.core.ForgeApp;
import io.trigger.forge.android.core.ForgeEventListener;
import io.trigger.forge.android.core.ForgeFile;
import io.trigger.forge.android.core.ForgeLog;
import io.trigger.forge.android.core.ForgeWebView;

import java.io.IOException;
import java.io.InputStream;
import java.net.MalformedURLException;
import java.net.ServerSocket;
import java.net.URL;
import java.security.KeyStore;

import javax.net.ssl.KeyManagerFactory;


public class EventListener extends ForgeEventListener {
	private static ForgeHttpd server = null;
	private static int port = 44300;
	
	private static int findFreePort() {
		ServerSocket socket = null;
		try {
			socket = new ServerSocket(0);
			socket.setReuseAddress(true);
			int port = socket.getLocalPort();
			try {
				socket.close();
			} catch (IOException e) {}
			ForgeLog.d("Found free network port: " + port);
			return port;
		} catch (IOException e) { 
		} finally {
			if (socket != null) {
				try {
					socket.close();
				} catch (IOException e) {}
			}
		}
		throw new IllegalStateException("Could not find a free port to start httpd on");
	}


	private static boolean startServer() {
        // Get config
        JsonObject config = new JsonObject();
        if (ForgeApp.appConfig.has("core")
                && ForgeApp.appConfig.getAsJsonObject("core").has("general")
                && ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").has("httpd")) {
            config = ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").getAsJsonObject("httpd");
        }

        // Set port
        port = 44300;
        if (config.has("port")) {
            port = config.get("port").getAsInt();
            if (port == 0) {
                try {
                    port = findFreePort();
                } catch (IllegalStateException e) {
                    ForgeLog.d("Could not find a free port to start httpd on.");
                    ForgeLog.e(e.getLocalizedMessage());
                    return false;
                }
            }
        }

        // Create server
        try {
            server = new ForgeHttpd("localhost", port);

            // Configure SSL
            Context context = ForgeApp.getActivity();
            InputStream certificate_stream = context.getResources().openRawResource(R.raw.localhost);
            String certificate_password = "insecure";

            if (config.has("certificate_path") && config.has("certificate_password")) {
                String certificate_path = config.get("certificate_path").getAsString();
                ForgeFile forgeFile = new ForgeFile(ForgeStorage.EndpointId.Source, certificate_path);
                // TODO forgeFile.getContents()
                AssetFileDescriptor fileDescriptor = ForgeStorage.getFileDescriptor(forgeFile);
                certificate_stream = fileDescriptor.createInputStream();
                certificate_password = config.get("certificate_password").getAsString();
                ForgeLog.d("Configured httpd to use custom certificate: " + certificate_path);
            }

            KeyStore keyStore = KeyStore.getInstance("pkcs12");
            keyStore.load(certificate_stream, certificate_password.toCharArray());
            KeyManagerFactory keyManagerFactory = KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());
            keyManagerFactory.init(keyStore, certificate_password.toCharArray());

            server.makeSecure(NanoHTTPD.makeSSLSocketFactory(keyStore, keyManagerFactory));
            ForgeLog.d("Configured httpd to use SSL");

        } catch (Exception e) {
            e.printStackTrace();
            ForgeLog.e("Failed to configure httpd: " + e.getLocalizedMessage());
            return false;
        }

        // startup web server
        try {
            server.start();
            ForgeLog.d("Started httpd on port " + port);
        } catch (Exception e) {
            ForgeLog.e("Failed to start httpd: " + e.getLocalizedMessage());
            return false;
        }

	    return true;
    }


    // = Life-cycle ===========================================================
	
	/**
	 * @hide
	 */
	@Override
	public void onStop() {
        if (server == null) {
            ForgeLog.e("Failed to pause httpd: Server is not initialized");
            return;
        }

        try {
            server.stop();
            ForgeLog.d("Pausing httpd while application not focused.");
        } catch (Exception e) {
            ForgeLog.e("Failed to pause httpd: " + e);
        }
	}
	

	/**
	 * @hide
	 */
	@Override
	public void onRestart() {
		if (server == null) {
            ForgeLog.e("Failed to restart httpd: Server is not initialized");
            return;
        }

		try {
			server.start();
			ForgeLog.d("Application in focus, resuming httpd.");			
		} catch (Exception e) {
			ForgeLog.e("Failed to restart httpd: " + e);
		}
	}


	// = onLoadInitialPage ====================================================

    @Override
    public Boolean onLoadInitialPage(final ForgeWebView webView) {
        if (!startServer()) {
            ForgeLog.e("Failed to start server for httpd module");
            return false;
        }

        // Load initial page
        try {
            String url = EventListener.getURL().toString();
            ForgeLog.d("httpd loading initial page: " + url);
            ForgeApp.getActivity().gotoUrl(url);
        } catch (Exception e) {
            ForgeLog.e("Failed to start server for httpd module: " + e.getLocalizedMessage());
            return false;
        }

        return true;
    }

    public static URL getURL() {
        // Read config
        JsonObject config = new JsonObject();
        if (ForgeApp.appConfig.has("core")
                && ForgeApp.appConfig.getAsJsonObject("core").has("general")) {
            config = ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general");
        }

        // Check if src/config.json has a custom url configured
        URL url = null;
        if (config.has("url")) {
            String configURL = config.get("url").getAsString();
            try {
                url = new URL(configURL);
            } catch (MalformedURLException e) {
                ForgeLog.e("Forge httpd cannot parse url from src/config.json: " + configURL);
            }
            return url;
        }

        // Fallback to default URL
        String defaultURL = "https://localhost:" + port + "/src/index.html";
        try {
            url = new URL(defaultURL);
        } catch (MalformedURLException e) {
            ForgeLog.e("Forge httpd cannot parse default URL: " + defaultURL);
        }

        return url;
    }
}
