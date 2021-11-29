package io.trigger.forge.android.modules.logging;

import com.google.gson.JsonObject;

import io.trigger.forge.android.core.ForgeLog;
import io.trigger.forge.android.core.ForgeParam;
import io.trigger.forge.android.core.ForgeTask;

public class API {
	private static JsonObject tag = null;

	public static void log(final ForgeTask task, @ForgeParam("message") final String message) {
		int level = 20;
		if (task.params.has("level") && task.params.getAsJsonPrimitive("level").isNumber()) {
			level = task.params.get("level").getAsInt();
		}

		switch (level) {
		case 10:
			ForgeLog.d(message);
			break;
		case 20:
			ForgeLog.i(message);
			break;
		case 30:
			ForgeLog.w(message);
			break;
		case 40:
			ForgeLog.e(message);
			break;
		case 50:
			ForgeLog.c(message);
			break;
		default:
			ForgeLog.i(message);
		}

		if (tag == null) {
			tag = new JsonObject();
			tag.addProperty("method", "logging.log");
		}

		task.success(tag);
	}
}
