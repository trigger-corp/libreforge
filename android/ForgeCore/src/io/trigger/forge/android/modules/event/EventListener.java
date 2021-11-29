package io.trigger.forge.android.modules.event;

import io.trigger.forge.android.core.ForgeApp;
import io.trigger.forge.android.core.ForgeEventListener;
import io.trigger.forge.android.core.ForgeLog;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Bundle;
import android.util.DisplayMetrics;
import android.view.KeyEvent;

import com.google.gson.JsonObject;

public class EventListener extends ForgeEventListener {
	protected static boolean preventDefaultBackAction = false;
	private BroadcastReceiver receiver;
	private IntentFilter filter = new IntentFilter("android.net.conn.CONNECTIVITY_CHANGE");

	@Override
	public void onCreate(Bundle savedInstanceState) {
		preventDefaultBackAction = false;
		receiver = new BroadcastReceiver() {
			@Override
			public void onReceive(Context context, Intent intent) {
				ConnectivityManager cm = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);

				NetworkInfo activeNetwork = cm.getActiveNetworkInfo();

				JsonObject result = new JsonObject();
				result.addProperty("connected", activeNetwork != null && activeNetwork.isConnected());
				result.addProperty("wifi", activeNetwork != null && activeNetwork.getType() == ConnectivityManager.TYPE_WIFI);
				ForgeApp.event("internal.connectionStateChange", result);
			}
		};
	}

	@Override
	public void onStop() {
		ForgeApp.getActivity().unregisterReceiver(receiver);
		ForgeApp.event("event.appPaused", null);
	}

	@Override
	public void onStart() {
		ForgeApp.getActivity().registerReceiver(receiver, filter);
	}

	@Override
	public void onRestart() {
		ForgeApp.event("event.appResumed", null);
	}
	
	@Override
	public Boolean onKeyDown(int keyCode, KeyEvent event) {
		if (!ForgeApp.getActivity().hasModalView) {
			if (keyCode == KeyEvent.KEYCODE_BACK) {
				if (!preventDefaultBackAction) {
					if (ForgeApp.getActivity().webView != null && ForgeApp.getActivity().webView.canGoBack()) {
						ForgeLog.i("Back button pressed, navigating to previous URL.");
						ForgeApp.getActivity().webView.goBack();
					} else {
						ForgeLog.i("Back button pressed, closing activity.");
						ForgeApp.getActivity().moveTaskToBack(true);
					}
				}
				ForgeApp.event("event.backPressed");
				return true;
			} else if (keyCode == KeyEvent.KEYCODE_MENU) {
				ForgeLog.i("Menu button pressed, triggering menu event.");
				ForgeApp.event("event.menuPressed");
				return true;
			}
		}
		return null;
	}

	@Override
	public void onKeyboardDidShow(float height) {
		DisplayMetrics displayMetrics = new DisplayMetrics();
		ForgeApp.getActivity().getWindowManager().getDefaultDisplay().getMetrics(displayMetrics);
		final float density = displayMetrics.density;

        JsonObject result = new JsonObject();
        result.addProperty("height", (int)(height / density));
        ForgeApp.event("event.keyboardDidShow", result);
	}

	@Override
	public void onKeyboardDidHide() {
        JsonObject result = new JsonObject();
        result.addProperty("height", 0.0f);
        ForgeApp.event("event.keyboardDidHide", result);
	}
}
