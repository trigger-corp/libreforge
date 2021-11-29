package io.trigger.forge.android.core;

import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

import android.webkit.JavascriptInterface; 

/**
 * @hide
 */
public class ForgeJSBridge {
	// Run tasks on threads from this thread pool, otherwise they block JS execution.
	private static ThreadPoolExecutor executor = new ThreadPoolExecutor(4, 4, 0, TimeUnit.MILLISECONDS, new LinkedBlockingQueue<Runnable>());
	
	private ForgeWebView webView;
	
	public ForgeJSBridge(ForgeWebView webView) {
		this.webView = webView;
	}
	
	@JavascriptInterface
	public void callJavaFromJavaScript(final String callid, final String method, final String params) {
		executor.execute(new Runnable() {
			public void run() {
				ForgeApp.callJavaFromJavaScript(webView, callid, method, params);
			}
		});
	}	
}
