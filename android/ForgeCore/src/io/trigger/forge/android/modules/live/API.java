package io.trigger.forge.android.modules.live;

import io.trigger.forge.android.core.ForgeApp;
import io.trigger.forge.android.core.ForgeLog;
import io.trigger.forge.android.core.ForgeTask;

public class API {
	public static void restartApp(final ForgeTask task) {
		task.performAsync(new Runnable() {
			public void run() {
				if (ForgeApp.appConfig.has("core")
						&& ForgeApp.appConfig.getAsJsonObject("core").has("general")
						&& ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").has("live")
						&& ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").getAsJsonObject("live").has("enabled")
						&& ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general").getAsJsonObject("live").get("enabled").getAsBoolean()) {
					Util.restartActivity();
				} else {										
					ForgeApp.getActivity().loadInitialPage();
				}
				
			}
		});
	}
}
