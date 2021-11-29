package io.trigger.forge.android.modules.reload;

import io.trigger.forge.android.core.ForgeApp;
import io.trigger.forge.android.core.ForgeLog;
import io.trigger.forge.android.core.ForgeTask;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.net.MalformedURLException;
import java.net.URL;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Map.Entry;
import java.util.Vector;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.NetworkInfo.DetailedState;

import com.google.common.base.Charsets;
import com.google.common.base.Throwables;
import com.google.common.io.Files;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParseException;
import com.google.gson.JsonParser;

final class HashMismatchException extends Exception {
	private static final long serialVersionUID = -1286362039069424879L;
}

public class Util {
	private static int updateDelay = 1; // milliseconds to wait before retrying
	private static final Object updateLock = new Object();
	private static long updatingThread = -1;
	
	public static boolean updateAvailable(Context context) {
		ForgeLog.i("Checking for reload update.");
		File liveFolder = context.getDir("reload-live", Context.MODE_PRIVATE);
		String snapshotId = "0";
		try {
			snapshotId = Files.readFirstLine(new File(liveFolder, "snapshot"), Charsets.UTF_8);
		} catch (IOException e) {
		}
		SharedPreferences prefs = context.getSharedPreferences("reload", 0);
		String streamId = prefs.getString("stream", "default");
		String installId = prefs.getString("install-id", "unknown");
		String versionCode = prefs.getString("version-code", "0");
		BufferedReader reader = null;
		try {
			String trigger_domain = "https://trigger.io";
			if (ForgeApp.appConfig.has("trigger_domain")) {
				trigger_domain = ForgeApp.appConfig.get("trigger_domain").getAsString();
			}
			String uuid = ForgeApp.appConfig.get("uuid").getAsString();
			String config_hash = ForgeApp.appConfig.get("config_hash").getAsString();
			URL url = new URL(trigger_domain + "/api/reload/" + uuid + "/updates/latest/" + streamId + "/" + config_hash + "/" + snapshotId + "/" + installId + "/" + versionCode);
			reader = new BufferedReader(new InputStreamReader(url.openStream()));
			JsonObject response = (JsonObject) new JsonParser().parse(reader.readLine());
			if (response.get("result").getAsString().equals("ok") && !response.get("latest").getAsBoolean()) {
				ForgeLog.i("Reload update available.");
				return true;
			}
		} catch (IOException e) {
		} finally {
			if (reader != null) {
				try {
					reader.close();
				} catch (IOException e) {
				}
			}
		}
		ForgeLog.i("No reload update available.");
		return false;
	}

	public static void applyNow(Context context, ForgeTask task) {
		ForgeApp.nativeEvent("onReloadUpdateApply", new Object[]{});
		ForgeLog.i("Attempting to apply reload app update.");
		Vector<String> hashes = new Vector<String>();
		File updateFolder = context.getDir("reload-update", Context.MODE_PRIVATE);
		// Check state is ok
		File updateState = new File(updateFolder, "state");
		if (updateState.exists()) {
			// Update in some state, decide what to do with it
			try {
				String state = Files.readFirstLine(updateState, Charsets.UTF_8);
				if (state == null || !state.equals("complete")) {
					if (task != null) {
						task.error("No completed update available", "EXPECTED_FAILURE", null);
					}
					ForgeLog.w("reload update failed: No completed update available.");
					return;
				}
			} catch (IOException e) {
				if (task != null) {
					task.error("Error reading update state", "UNEXPECTED_FAILURE", null);
				}
				ForgeLog.w("reload update failed: Error reading update state.");
				return;
			}
		} else {
			if (task != null) {
				task.error("No completed update available", "EXPECTED_FAILURE", null);
			}
			ForgeLog.w("reload update failed: No completed update available.");
			return;
		}
		File manifestFile = new File(updateFolder, "manifest");
		if (manifestFile.exists()) {
			BufferedReader reader = null;
			try {
				reader = new BufferedReader(new FileReader(manifestFile));
				StringBuilder sb = new StringBuilder();
				String line;
				while ((line = reader.readLine()) != null) {
					sb.append(line);
				}
				String manifestStr = sb.toString();
				JsonObject manifest = new JsonParser().parse(manifestStr).getAsJsonObject();
				
				for (Entry<String, JsonElement> entry : manifest.entrySet()) {
					String fileUrl = entry.getValue().getAsString();
					hashes.add(getLastPathComponent(fileUrl));
				}
			} catch (IOException e) {
				if (task != null) {
					task.error("Error reading update state", "UNEXPECTED_FAILURE", null);
				}
				ForgeLog.w("reload update failed: Error reading update state.");
				return;
			} catch (JsonParseException e) {
				if (task != null) {
					task.error("Error reading update state", "UNEXPECTED_FAILURE", null);
				}
				ForgeLog.w("reload update failed: Error reading update manifest, update will redownload.");
				retryUpdate(context);
				return;
			} finally {
				if (reader != null) {
					try {
						reader.close();
					} catch (IOException e) {
					}
				}
			}
		} else {
			if (task != null) {
				task.error("Error reading update state", "UNEXPECTED_FAILURE", null);
			}
			ForgeLog.w("reload update failed: Manifest does not exist, update will redownload.");
			retryUpdate(context);
			return;
		}
		File liveFolder = context.getDir("reload-live", Context.MODE_PRIVATE);

		String[] inLive = liveFolder.list();
		// Delete any files not in the new manifest
		for (String file : inLive) {
			if (!hashes.contains(file)) {
				new File(liveFolder, file).delete();
			}
		}
		// Move everything in update to live
		String[] inUpdate = updateFolder.list();
		for (String file : inUpdate) {
			new File(updateFolder, file).renameTo(new File(liveFolder, file));
		}
		if (task != null) {
			task.success();
		}
		ForgeLog.i("Update applied successfully.");
	}

	public static void updateWithLock(Context context, final ForgeTask task) {
		synchronized (Util.updateLock) {
			if (updatingThread >= 0 && updatingThread != Thread.currentThread().getId()) {
				String message = "Reload update already in progress: not proceeding";
				if (task != null) {
					task.error(message, "EXPECTED_FAILURE", null);
				}
				ForgeLog.w(message);
				return; 
			}
			updatingThread = Thread.currentThread().getId();
		}
		ForgeLog.i("Starting reload update.");
		
		Util.update(context, task);
		
		synchronized (Util.updateLock) {
			updatingThread = -1;
		}
	}	

	private static void update(Context context, final ForgeTask task) {
		File liveFolder = context.getDir("reload-live", Context.MODE_PRIVATE);
		File updateFolder = context.getDir("reload-update", Context.MODE_PRIVATE);
		File updateState = new File(updateFolder, "state");
		if (updateState.exists()) {
			String state = Util.getUpdateState(context);
			if (state != null && state.equals("complete")) {
				// Update already waiting to be applied
				if (task != null) {
					task.success();
				}
				ForgeLog.i("reload update downloaded and ready to apply.");
				ForgeApp.event("reload.updateReady", null);
				return;
			}
			if ("paused".equals(state)) {
				String message = "Reload updates are paused: call 'update' to resume";
				if (task != null) {
					// shouldn't get here - if we have a task, it's an explicit update,
					// rather than caused by app state change, but just in case...
					task.error(message, "EXPECTED_FAILURE", null);
				}
				ForgeLog.i(message);
				return;
			}
			
			// Check for manifest
			File manifestFile = new File(updateFolder, "manifest");
			if (manifestFile.exists()) {
				// Update underway - attempt to resume
				ForgeLog.i("Resuming previous incomplete reload update.");
				downloadUpdateFiles(context);
			} else {
				// Update has gone wrong - wipe and retry
				ForgeLog.i("Don't have a Reload manifest: cleaning and attempting fresh update.");
				String[] inUpdate = updateFolder.list();
				for (String file : inUpdate) {
					new File(updateFolder, file).delete();
				}
				updateWithLock(context, task);
			}
		} else {
			// Clean update
			String snapshotId = "0";
			BufferedReader snapshotIdReader = null;
			try {
				snapshotIdReader = new BufferedReader(new FileReader(new File(liveFolder, "snapshot")));
				snapshotId = snapshotIdReader.readLine();
			} catch (IOException e) {
			} finally {
				if (snapshotIdReader != null) {
					try {
						snapshotIdReader.close();
					} catch (IOException e) {
					}
				}
			}
			SharedPreferences prefs = context.getSharedPreferences("reload", 0);
			String streamId = prefs.getString("stream", "default");
			String manifestUrl = null;
			BufferedReader reader = null;
			try {
				URL url = new URL(ForgeApp.appConfig.get("trigger_domain").getAsString() + "/api/reload/" + ForgeApp.appConfig.get("uuid").getAsString() + "/updates/" + streamId + "/" + ForgeApp.appConfig.get("config_hash").getAsString() + "/" + snapshotId);
				reader = new BufferedReader(new InputStreamReader(url.openStream()));
				JsonObject response = (JsonObject) new JsonParser().parse(reader.readLine());
				if (response.get("result").getAsString().equals("ok")) {
					JsonObject snapshot = response.getAsJsonObject("snapshot");
					if (!snapshot.has("manifest_url")) {
						if (task != null) {
							task.error("No update available", "EXPECTED_FAILURE", null);
						}
						ForgeLog.i("No reload update available");
						return;
					}
					snapshotId = snapshot.get("id").getAsString();
					manifestUrl = snapshot.get("manifest_url").getAsString();
				} else {
					if (task != null) {
						task.error("Failed to download update details: " + response.get("text").getAsString(), "EXPECTED_FAILURE", null);
					}
					ForgeLog.i("Server-side error while downloading Reload update details: " + response.get("text").getAsString());
					return;
				}
			} catch (MalformedURLException e) {
				ForgeLog.i("Failed to download reload update details: " + Throwables.getStackTraceAsString(e));
				if (task != null) {
					task.error(e);
				}
				return;
			} catch (IOException e) {
				ForgeLog.i("Failed to download reload update details: " + Throwables.getStackTraceAsString(e));
				if (task != null) {
					task.error(e);
				}
				return;
			} catch (JsonParseException e) {
				ForgeLog.i("Failed to download reload update details: " + Throwables.getStackTraceAsString(e));
				if (task != null) {
					task.error(e);
				}
				return;
			} finally {
				if (reader != null) {
					try {
						reader.close();
					} catch (IOException e) {
					}
				}
			}
			if (manifestUrl == null) {
				// This shouldn't happen, but just in case...
				ForgeLog.i("Unknown update error");
				if (task != null) {
					task.error("Unknown update error");
				}
				return;
			}
			if (task != null) {
				task.success();
			}

			File manifestFile = new File(updateFolder, "manifest");
			boolean downloaded = false;
			try {
				downloaded = downloadFile(manifestUrl, manifestFile);
			} catch (MalformedURLException e) {
				// really bad: we've been pointed at a mangled manifest URL
				// clear out and start again - this will constantly fail until the
				// manifest URL is corrected!
				ForgeLog.w("Couldn't download Reload manifest from " + manifestUrl + " - Reload is broken until this is fixed!");
				retryUpdate(context);
				if (task != null) {
					task.error("Manifest URL is invalid", "EXPECTED_FAILURE", null);
				}
				return;
			} catch (HashMismatchException e) {
				// a Reloader has got the hash of file wrong (or network corruption)
				// on the safe side, clear out and start again
				retryUpdate(context);
				if (task != null) {
					task.error("Hash mismatch for Reload file", "EXPECTED_FAILURE", null);
				}
				return;
			}
			if (!downloaded) {
				ForgeLog.w("Error downloading reload update manifest");
				retryUpdate(context);
				if (task != null) {
					task.error("Manifest URL is invalid", "EXPECTED_FAILURE", null);
				}
				return;
			}
			try {
				File snapshotFile = new File(updateFolder, "snapshot");
				PrintWriter writer = new PrintWriter(snapshotFile);
				writer.print(snapshotId);
				writer.close();
			} catch (FileNotFoundException e) {
				ForgeLog.w(Throwables.getStackTraceAsString(e));
			}
			try {
				updateState.createNewFile();
			} catch (IOException e) {
			}
			downloadUpdateFiles(context);
		}
	}

	private static void downloadUpdateFiles(Context context) {
		File liveFolder = context.getDir("reload-live", Context.MODE_PRIVATE);
		File updateFolder = context.getDir("reload-update", Context.MODE_PRIVATE);
		File manifestFile = new File(updateFolder, "manifest");

		JsonObject hash_to_file = new JsonObject();
		try {
			InputStreamReader reader = new InputStreamReader(context.getAssets().open("hash_to_file.json"), "UTF-8");
			BufferedReader br = new BufferedReader(reader);
			String hash_to_file_string = br.readLine();
			br.close();
			hash_to_file = (JsonObject) new JsonParser().parse(hash_to_file_string);
		} catch (IOException e) {
			ForgeLog.w(Throwables.getStackTraceAsString(e));
		}

		if (!manifestFile.exists()) {
			ForgeLog.w("No reload manifest found. Aborting download of update files.");
			return;
		}

		try {
			JsonObject manifest = new JsonParser().parse(Files.toString(manifestFile, Charsets.UTF_8)).getAsJsonObject();

			Vector<String> urlsToDownload = new Vector<String>();
			for (Entry<String, JsonElement> entry : manifest.entrySet()) {
				String fileUrl = entry.getValue().getAsString();
				String hash = getLastPathComponent(fileUrl);
				if (!new File(updateFolder, hash).exists() && !new File(liveFolder, hash).exists() && !hash_to_file.has(hash)) {
					urlsToDownload.add(fileUrl);
				}
			}
			ForgeLog.d("We have " + urlsToDownload.size() + " Reload files to download");

			JsonObject progressParams = new JsonObject();
			progressParams.addProperty("total", urlsToDownload.size());
			progressParams.addProperty("completed", 0);
			for (String fileUrl : urlsToDownload) {
				if ("paused".equals(getUpdateState(context))) {
					ForgeLog.i("Pausing Reload update: call 'update' to resume...");
					return;
				}

				String hash = getLastPathComponent(fileUrl);
				boolean fileDownloaded = false;
				try {
					 fileDownloaded = downloadFile(fileUrl, new File(updateFolder, hash));
				} catch (MalformedURLException e) {
					// pretty bad: a mangled download URL is in the manifest - need to clear out the manifest
					// and retry to pick up a fixed update
					ForgeLog.w("Couldn't download Reload update file from " + fileUrl);
					retryUpdate(context);
					return;
				} catch (HashMismatchException e) {
					// a Reloader has got the hash of file wrong (or network corruption)
					// on the safe side, clear out and start again
					ForgeLog.w("Couldn't verify Reload update from " + fileUrl);
					retryUpdate(context);
					return;
				}
				if (!fileDownloaded) {
					ForgeLog.w("Error downloading reload update file, will reattempt on next app start.");
					retryUpdate(context);
					return;
				} else {
					progressParams.addProperty("completed",  progressParams.get("completed").getAsInt() + 1);
					ForgeApp.event("reload.updateProgress", progressParams);
				}
			}

			// All files downloaded
			PrintWriter writer = new PrintWriter(new File(updateFolder, "state"));
			writer.print("complete");
			writer.close();
			ForgeLog.i("reload update downloaded and ready to apply.");
			ForgeApp.event("reload.updateReady", null);
		} catch (IOException e) {
			ForgeLog.w("Error downloading reload update file, will reattempt on next app start.");
		} catch (JsonParseException e) {
			retryUpdate(context);
		}

	}

	private static void retryUpdate(Context context) {
		// Update has gone wrong - wipe and retry
		File updateFolder = context.getDir("reload-update", Context.MODE_PRIVATE);
		
		ForgeLog.d("Backing off Reload retry for "+getUpdateDelay()+"ms");
		try {
			Thread.sleep(getUpdateDelay());
		} catch (InterruptedException e) {
			ForgeLog.d("Continuing...");
		}
		increaseUpdateDelay();
		ForgeLog.i("Previous reload update corrupted, cleaning and attempting fresh update.");
		String[] inUpdate = updateFolder.list();
		for (String file : inUpdate) {
			new File(updateFolder, file).delete();
		}
		updateWithLock(context, null);
	}

	private static boolean downloadFile(String from, File to) throws MalformedURLException, HashMismatchException {
		ForgeLog.d("Attempting to download reload file: " + from);
		File tempfile = new File(to.toString() + "_");
		java.net.URL url;
		url = new java.net.URL(from);
		try {
			InputStream input = url.openStream();
			OutputStream output = new FileOutputStream(tempfile);
			try {
				MessageDigest md = MessageDigest.getInstance("SHA1");
				byte[] buffer = new byte[1024];
				int bytesRead = 0;
				while ((bytesRead = input.read(buffer, 0, buffer.length)) >= 0) {
					md.update(buffer, 0, bytesRead);
					output.write(buffer, 0, bytesRead);
				}
				byte[] mdbytes = md.digest();
				StringBuffer sb = new StringBuffer("");
				for (byte mdbyte : mdbytes) {
					sb.append(Integer.toString((mdbyte & 0xff) + 0x100, 16).substring(1));
				}
				String filename = from.substring(from.lastIndexOf("/") + 1);
				if (sb.toString().equals(filename)) {
					tempfile.renameTo(to);
					ForgeLog.d("reload download successful");
					return true;
				} else {
					ForgeLog.w("Hash mismatch: "+sb.toString()+" vs "+filename);
					throw new HashMismatchException();
				}
			} catch (NoSuchAlgorithmException e) {
				ForgeLog.w("SHA1 not available");
			} finally {
				output.close();
				input.close();
			}
		} catch (IOException e) {
			ForgeLog.w(Throwables.getStackTraceAsString(e));
		} finally {
			if (tempfile.exists()) {
				tempfile.delete();
				ForgeLog.w("reload download failed");
				return false;
			} else {
			}
		}
		ForgeLog.w("reload download failed");
		return false;
	}
	
	static String getUpdateState(Context context) {
		File updateFolder = context.getDir("reload-update", Context.MODE_PRIVATE);
		File updateState = new File(updateFolder, "state");
		if (updateState.exists()) {
			BufferedReader reader = null;
			try {
				reader = new BufferedReader(new FileReader(updateState));
				return reader.readLine();
			} catch (FileNotFoundException e) {
				// clean update
				return null;
			} catch (IOException e) {
				ForgeLog.w(Throwables.getStackTraceAsString(e));
				return null;
			} finally {
				if (reader != null) {
					try {
						reader.close();
					} catch (IOException e) {
						ForgeLog.w(Throwables.getStackTraceAsString(e));
					}
				}
			}
		}
		return null;
	}
	
	static void setUpdateState(Context context, String state) {
		File updateFolder = context.getDir("reload-update", Context.MODE_PRIVATE);
		PrintWriter writer;
		try {
			File stateFile = new File(updateFolder, "state");
			if (!stateFile.isFile()) {
				stateFile.createNewFile();
			}
			writer = new PrintWriter(stateFile);
			writer.print(state);
			writer.close();
		} catch (FileNotFoundException e) {
			Throwables.getStackTraceAsString(e);
		} catch (IOException e) {
			Throwables.getStackTraceAsString(e);
		}
	}
	
	private static int getUpdateDelay() {
		return updateDelay;
	}
	/** exponentially increase backoff */
	private static void increaseUpdateDelay() {
		if (updateDelay * 2 < 1000 * 60 * 60) {
			updateDelay *= 2;
		}
	}
	
	private static String getLastPathComponent(String url) throws MalformedURLException {
		URL parsedFileUrl = new URL(url);
		String path = parsedFileUrl.getPath();
		return path.substring(path.lastIndexOf("/") + 1);
	}

	static boolean reloadManual() {
		if (!(ForgeApp.appConfig.has("core") && ForgeApp.appConfig.getAsJsonObject("core").has("general"))) {
			return false;
		}
		JsonObject config = ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general");
		boolean reload = config.has("reload") ? config.get("reload").getAsBoolean() : false;
		if (!reload) {
			return false;
		}
		boolean reload_manual = config.has("reload_manual") ? config.get("reload_manual").getAsBoolean() : false;
		if (reload_manual) {
			ForgeLog.d("Reload's automated functionality has been disabled.");
		}
		return reload_manual;
	}
	
	static boolean reloadEnabled() {		
		if (!(ForgeApp.appConfig.has("core") && ForgeApp.appConfig.getAsJsonObject("core").has("general"))) {
			return false;
		}		
		JsonObject config = ForgeApp.appConfig.getAsJsonObject("core").getAsJsonObject("general");
		boolean reload = config.has("reload") ? config.get("reload").getAsBoolean() : false;
		if (!reload) {
			return false;
		}		
		boolean forcewifi = config.has("reload_forcewifi") ? config.get("reload_forcewifi").getAsBoolean() : false;
		
		ConnectivityManager manager = (ConnectivityManager)ForgeApp.getActivity().getApplicationContext().getSystemService(Context.CONNECTIVITY_SERVICE);
		NetworkInfo wifi = manager.getNetworkInfo(ConnectivityManager.TYPE_WIFI);
		NetworkInfo mobile = manager.getNetworkInfo(ConnectivityManager.TYPE_MOBILE);
		
		if (wifi.isAvailable() && wifi.getDetailedState() == DetailedState.CONNECTED) {
			ForgeLog.d("Reload has WiFi network connectivity");
			return true;
		} else if (mobile.isAvailable() && mobile.getDetailedState() == DetailedState.CONNECTED) {
			ForgeLog.d("Reload has Mobile network connectivity: " + forcewifi);
			return (forcewifi == false);
		} else {
			ForgeLog.d("Reload has no network connectivity");
			return false;
		}
	}
}
