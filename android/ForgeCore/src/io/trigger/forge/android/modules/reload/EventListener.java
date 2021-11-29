package io.trigger.forge.android.modules.reload;

import io.trigger.forge.android.core.ForgeApp;
import io.trigger.forge.android.core.ForgeEventListener;
import io.trigger.forge.android.core.ForgeLog;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.UUID;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.SharedPreferences.Editor;
import android.content.pm.PackageManager.NameNotFoundException;
import android.os.AsyncTask;
import android.os.Bundle;

public class EventListener extends ForgeEventListener {
	@Override
	public void onCreate(Bundle savedInstanceState) {
		// Unique user id
		SharedPreferences prefs = ForgeApp.getActivity().getSharedPreferences("reload", 0);
		if (!prefs.contains("install-id")) {
			Editor edit = prefs.edit();
			edit.putString("install-id", UUID.randomUUID().toString());
			edit.commit();
		}
		String versionCode = "1";
		try {
			versionCode = String.valueOf(ForgeApp.getActivity().getPackageManager().getPackageInfo(ForgeApp.getActivity().getPackageName(), 0).versionCode);
		} catch (NameNotFoundException e1) {
		}

		// Use config.json because we can no longer munge AndroidManifest.xml after binary compiles
		// TODO deprecate check in manifest above when we ship v2.5
		if (ForgeApp.appConfig.has("version_code")) {
			versionCode = ForgeApp.appConfig.get("version_code").getAsString();
		}

		if (!versionCode.equals(prefs.getString("version-code", "0"))) {
			// New version, clear any reload updates
			ForgeLog.i("New app version. removing any reload update files.");
			// Delete any live updates
			File liveFolder = ForgeApp.getActivity().getDir("reload-live", Context.MODE_PRIVATE);
			String[] inUpdate = liveFolder.list();
			for (String file : inUpdate) {
				new File(liveFolder, file).delete();
			}
			// Delete any partial updates - which will no longer be applicable
			File updateFolder = ForgeApp.getActivity().getDir("reload-update", Context.MODE_PRIVATE);
			inUpdate = updateFolder.list();
			for (String file : inUpdate) {
				new File(updateFolder, file).delete();
			}
		}
		// Save current version code
		Editor edit = prefs.edit();
		edit.putString("version-code", versionCode);
		edit.commit();

		// Apply an update if one is available
		// Here as well as onStart so if possible it will apply before the webview is loaded
		File updateFolder = ForgeApp.getActivity().getDir("reload-update", Context.MODE_PRIVATE);
		File updateState = new File(updateFolder, "state");
		if (updateState.exists() && !Util.reloadManual()) {
			BufferedReader reader;
			try {
				reader = new BufferedReader(new FileReader(updateState));
				String state = reader.readLine();
				if (state != null && state.equals("complete")) {
					Util.applyNow(ForgeApp.getActivity(), null);
				}
			} catch (IOException e) {
			}
		}

		// Try to update
		if (Util.reloadEnabled() && !Util.reloadManual()) {
			new AsyncTask<Object, Object, Object>() {
				@Override
				protected Object doInBackground(Object... arg0) {
					try {
						// Wait until the app has loaded before attempting to update
						Thread.sleep(3000, 0);
						if (Util.updateAvailable(ForgeApp.getActivity())) {
							Util.updateWithLock(ForgeApp.getActivity(), null);
						}
					} catch (Exception e) {
					}
					return null;
				}
			}.execute();
		}
	}

	@Override
	public void onStop() {
		super.onStop();

		// Attempt to update on app hide
		if (Util.reloadEnabled() && !Util.reloadManual()) {
			new AsyncTask<Object, Object, Object>() {
				@Override
				protected Object doInBackground(Object... arg0) {
					try {
						if (Util.updateAvailable(ForgeApp.getActivity())) {
							Util.updateWithLock(ForgeApp.getActivity(), null);
						}
					} catch (Exception e) {
					}
					return null;
				}
			}.execute();
		}
	};

	@Override
	public void onStart() {
		// Apply reload update if it is ready

		File updateFolder = ForgeApp.getActivity().getDir("reload-update", Context.MODE_PRIVATE);
		File updateState = new File(updateFolder, "state");
		if (updateState.exists() && !Util.reloadManual()) {
			BufferedReader reader;
			try {
				reader = new BufferedReader(new FileReader(updateState));
				String state = reader.readLine();
				if (state != null && state.equals("complete")) {
					Util.applyNow(ForgeApp.getActivity(), null);
					ForgeApp.getActivity().loadInitialPage();
				}
			} catch (IOException e) {
			}
		}
	}
}
