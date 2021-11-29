package io.trigger.forge.android.core;

import android.content.Context;
import android.webkit.WebSettings;
import android.webkit.WebView;


public class ForgeWebView extends WebView {
	public ForgeWebView(Context context) {
		super(context);
	}
	public WebSettings getSettingsInternal() {
		return this.getSettings();
	}
}
