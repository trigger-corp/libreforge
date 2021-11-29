package io.trigger.forge.android.modules.templatemodule;

import io.trigger.forge.android.core.ForgeApp;
import io.trigger.forge.android.core.ForgeEventListener;

public class EventListener extends ForgeEventListener {
	@Override
	public void onRestart() {
		ForgeApp.event("templatemodule.resume", null);
	}
}
