package io.trigger.forge.android.modules.reload;

import io.trigger.forge.android.core.ForgeApp;
import io.trigger.forge.android.core.ForgeLog;
import io.trigger.forge.android.core.ForgeParam;
import io.trigger.forge.android.core.ForgeTask;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URL;

import android.content.SharedPreferences.Editor;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

public class API {
	public static void updateAvailable(final ForgeTask task) {
		task.performAsync(new Runnable() {
			public void run() {
				if (Util.reloadEnabled() && Util.updateAvailable(ForgeApp.getActivity())) {
					task.success(true);
				} else {
					task.success(false);
				}
			}
		});
	}

	public static void update(final ForgeTask task) {
		if (Util.reloadEnabled() && "paused".equals(Util.getUpdateState(ForgeApp.getActivity()))) {
			ForgeLog.i("Resuming Reload updates");
			Util.setUpdateState(ForgeApp.getActivity(), "");
		}
		task.performAsync(new Runnable() {
			public void run() {
				Util.updateWithLock(ForgeApp.getActivity(), task);
			}
		});
	}

	public static void applyAndRestartApp(final ForgeTask task) {
		task.performAsync(new Runnable() {
			public void run() {
				Util.applyNow(ForgeApp.getActivity(), task);
				ForgeApp.getActivity().loadInitialPage();
			}
		});
	}

	public static void switchStream(final ForgeTask task, @ForgeParam("streamid") final String streamid) {
		BufferedReader reader = null;
		InputStream is = null;
		try {
			if (!streamid.matches("^[a-z0-9_-]+$")) {
				task.error("Invalid stream name", "EXPECTED_FAILURE", null);
				return;
			}
			if (Util.reloadEnabled()) {
				URL url = new URL(ForgeApp.appConfig.get("trigger_domain").getAsString() + "/api/reload/" + ForgeApp.appConfig.get("uuid").getAsString() + "/streams/" + streamid);
				is = url.openStream();
				reader = new BufferedReader(new InputStreamReader(is));
				JsonObject response = (JsonObject) new JsonParser().parse(reader.readLine());
				if (response.get("result").getAsString().equals("ok")) {
					Editor prefs = ForgeApp.getActivity().getSharedPreferences("reload", 0).edit();
					prefs.putString("stream", streamid);
					prefs.commit();
					task.success();
				} else {
					task.error(response.get("text").getAsString(), "EXPECTED_FAILURE", null);
				}
			} else {
				task.error("Reload is disabled or device has no network connectivity");
			}
		} catch (IOException e) {
			task.error("Error contacting Reload service: " + e.getLocalizedMessage(), "EXPECTED_FAILURE", null);
		} finally {
			if (reader != null) {
				try {
					reader.close();
				} catch (IOException e) {
				}
			}
			if (is != null) {
				try {
					is.close();
				} catch (IOException e) {
				}
			}
		}
	}
	
	public static void pauseUpdate(final ForgeTask task) {
		Util.setUpdateState(ForgeApp.getActivity(), "paused");
	}
}
