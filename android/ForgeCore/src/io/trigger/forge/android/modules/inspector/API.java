package io.trigger.forge.android.modules.inspector;

import io.trigger.forge.android.core.ForgeApp;
import io.trigger.forge.android.core.ForgeTask;

public class API {
	public static void list(final ForgeTask task) {
		task.success(ForgeApp.getAPIMethodInfo());
	}
}
