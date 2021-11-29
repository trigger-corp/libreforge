package io.trigger.forge.android.modules.internal;

import io.trigger.forge.android.core.ForgeApp;
import io.trigger.forge.android.core.ForgeTask;
import android.app.AlertDialog;

public class API {
	private static AlertDialog debugWarning = null;

	public static void showDebugWarning(final ForgeTask task) {
		task.performUI(new Runnable() {
			public void run() {
				debugWarning = new AlertDialog.Builder(ForgeApp.getActivity()).create();
				debugWarning.setCancelable(false);
				debugWarning.setTitle("Waiting for Catalyst...");
				debugWarning.setMessage("Waiting for connection to Catalyst\n\nThis is because your code includes 'forge.enableDebug();'");
				debugWarning.show();
				task.success();
			}
		});
	}

	public static void hideDebugWarning(final ForgeTask task) {
		task.performUI(new Runnable() {
			public void run() {
				if (debugWarning != null) {
					debugWarning.dismiss();
					debugWarning = null;
				}
				task.success();
			}
		});
	}

	public static void ping(final ForgeTask task) {
		task.success(task.params.getAsJsonArray("data"));
	}
}
