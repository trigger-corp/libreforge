package io.trigger.forge.android.modules.event;

import io.trigger.forge.android.core.ForgeApp;
import io.trigger.forge.android.core.ForgeTask;

public class API {
	public static void backPressed_preventDefault(final ForgeTask task) {
		EventListener.preventDefaultBackAction = true;
		task.success();
	}
	public static void backPressed_restoreDefault(final ForgeTask task) {
		EventListener.preventDefaultBackAction = false;
		task.success();
	}
	public static void backPressed_closeApplication(final ForgeTask task) {
		ForgeApp.getActivity().webView = null;
		ForgeApp.getActivity().finish();
	}
	public static void backPressed_pauseApplication(final ForgeTask task) {
		ForgeApp.getActivity().moveTaskToBack(true);
	}
}
