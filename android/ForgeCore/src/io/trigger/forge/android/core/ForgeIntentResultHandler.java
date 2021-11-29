package io.trigger.forge.android.core;

import android.content.Intent;

/**
 * Class to hold a callback to handle the results from an Intent
 */
public abstract class ForgeIntentResultHandler {
	/**
	 * @hide
	 */
	public ForgeIntentResultHandler() {
	}
	/**
	 * Callback invoked on completion of Intent. See {@link android.app.Activity#onActivityResult}.
	 * 
	 * @param requestCode
	 * @param resultCode
	 * @param data
	 */
	public abstract void result(int requestCode, int resultCode, Intent data);
}
