package io.trigger.forge.android.core;

import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

import com.google.common.base.Throwables;
import com.google.gson.JsonElement;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;

/**
 * A ForgeTask contains details about a native API call from Javascript, and has several helper methods to perform common tasks from a native API call.
 */
public class ForgeTask {
	/**
	 * UUID for this task, to be returned with response.
	 */
	public final String callid;
	/**
	 * The parameters passed to this API call from Javascript.
	 */
	public final JsonObject params;
	/**
	 * The webview that initiated this task
	 */
	public final ForgeWebView webView;
	/**
	 * Whether or not the task has returned a result yet
	 */
	public boolean returned = false;
	
	/**
	 * @hide
	 */
	private static ThreadPoolExecutor executor = new ThreadPoolExecutor(4, 32, 5000, TimeUnit.MILLISECONDS, new LinkedBlockingQueue<Runnable>());

	/**
	 * Create a task
	 * 
	 * @param callid UUID for the task
	 * @hide
	 */
	public ForgeTask(String callid, JsonObject jsonParams, ForgeWebView webView) {
		this.callid = callid;
		this.params = jsonParams;
		this.webView = webView;
	}

	/**
	 * Return success with no data
	 */
	public void success() {
		success(JsonNull.INSTANCE);
	}

	/**
	 * Return success with data
	 * 
	 * @param result Any JSON serializable object to be returned
	 */
	public void success(JsonElement result) {
		returnResult("success", result);
	}
	
	public void success(String result) {
		success(new JsonPrimitive(result));
	}
	
	public void success(boolean result) {
		success(new JsonPrimitive(result));
	}

	/**
	 * Return an error with data
	 * 
	 * @param result Any JSON serializable object to be returned, requires a message property.
	 */
	public void error(JsonElement result) {
		returnResult("error", result);
	}
	
	public void error(String result) {
		error(new JsonPrimitive(result));
	}

	/**
	 * Return an error in the standard template
	 * 
	 * @param message Human readable error message
	 * @param type One of EXPECTED_FAILURE, UNEXPECTED_FAILRE, UAVAILABLE or BAD_INPUT
	 * @param subtype An optional easily matched constant for particular errors that may need to be sorted programmatically.
	 */
	public void error(String message, String type, String subtype) {
		JsonObject content = new JsonObject();
		content.addProperty("message", message);
		content.addProperty("type", type);
		content.addProperty("subtype", subtype);

		returnResult("error", content);
	}

	/**
	 * Return an error with the message from a Throwable. Useful for unexpected exceptions to ensure some feedback is sent to javascript.
	 * 
	 * @param error Any unexpected throwable
	 */
	public void error(Throwable error) {
		JsonObject content = new JsonObject();
		content.addProperty("message", "Forge Java error: " + error.getClass().getSimpleName() + ": " + error.getMessage());
		content.addProperty("type", "UNEXPECTED_FAILURE");
		content.add("subtype", JsonNull.INSTANCE);
		content.addProperty("full_error", Throwables.getStackTraceAsString(error));

		returnResult("error", content);
	}

	/**
	 * Perform an async task not on the main thread. By default Javascript API calls happen in the Javascript thread, any long running operation should be done asynchronously.
	 * 
	 * @param task task to perform
	 */
	public void performAsync(final Runnable task) {
		final ForgeTask jsTask = this;
		executor.execute(new Runnable() {
			public void run() {
				try {
					task.run();
				} catch (Exception e) {
					jsTask.error(e);
				}
			}
		});
	}

	/**
	 * Perform a task on the UI thread.
	 * 
	 * @param task task to perform
	 */
	public void performUI(final Runnable task) {
		final ForgeTask forgeTask = this;
		// Execute asynchronously.
		ForgeApp.getActivity().runOnUiThread(new Runnable() {
			public void run() {
				try {
					task.run();
				} catch (Exception e) {
					forgeTask.error(e);
				}
			}
		});
	}

	/**
	 * Return to Javascript
	 * 
	 * @param status
	 *            {success, error}
	 * @param content
	 *            JSON serializable return content
	 */
	private void returnResult(String status, JsonElement content) {
		JsonObject result = new JsonObject();
		result.add("content", content);
		result.addProperty("callid", callid);
		result.addProperty("status", status);

		ForgeApp.returnObject(webView, result);
		returned = true;
	}

    /**
     * Convenience method for requesting permissions
     *
     * @param permission Permission to request
     * @param completion Block to run on successful permission request
     */
    public void withPermission(final String permission, Runnable completion) {
        final ForgeTask self = this;
        ForgeApp.getActivity().requestPermission(permission, new ForgeActivity.EventAccessBlock() {
            @Override
            public void run(boolean granted) {
                if (!granted) {
                    self.error("Permission denied", "EXPECTED_FAILURE", null);
                    return;
                }
                completion.run();
            }
        });
    }
}
