package io.trigger.forge.android.core;

import android.content.Intent;
import android.content.res.Configuration;
import android.os.Bundle;
import android.view.ContextMenu;
import android.view.ContextMenu.ContextMenuInfo;
import android.view.KeyEvent;
import android.view.Menu;
import android.view.MenuItem;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager.LayoutParams;

/**
 * Plugin event listeners should extend this class, and implement any methods
 * they wish to handle events from.
 */
public abstract class ForgeEventListener {
	/**
	 * @hide
	 */
	public ForgeEventListener() {
	}

	/**
	 * Called when the activity is initially created. See
	 * {@link android.app.Activity#onCreate}.
	 */
	public void onCreate(Bundle savedInstanceState) {
	}

	/**
	 * Called when an app is created. See
	 * {@link android.app.Application#onCreate}.
	 */
	public void onApplicationCreate() {
	}
	
	/**
	 * Called when an app is destroyed. See
	 * {@link android.app.Activity#onDestroy}.
	 */
	public void onDestroy() {
	}

	/**
	 * Called after an app is created. See
	 * {@link android.app.Activity#onPostCreate}.
	 */
	public void onPostCreate(Bundle savedInstanceState) {
	}

	/**
	 * Called when an intent is received. See
	 * {@link android.app.Activity#onNewIntent}.
	 */
	public void onNewIntent(Intent intent) {
	}

	/**
	 * Called on key press event. See {@link android.app.Activity#onKeyDown}. If
	 * your plugin does not handle this event you must return null, otherwise
	 * other modules will not be given an opportunity to handle the event.
	 */
	public Boolean onKeyDown(int keyCode, KeyEvent event) {
		return false;
	}

	/**
	 * Called when an app is stopped. See {@link android.app.Activity#onStop}.
	 */
	public void onStop() {
	}

	/**
	 * Called when an app is started. See {@link android.app.Activity#onStart}.
	 */
	public void onStart() {
	}

	/**
	 * Called when an app is restarted. See
	 * {@link android.app.Activity#onRestart}.
	 */
	public void onRestart() {
	}

	/**
	 * Called when an receives an intent result. See
	 * {@link android.app.Activity#onActivityResult}.
	 * 
	 * @see ForgeApp#intentWithHandler
	 */
	public void onActivityResult(int requestCode, int resultCode, Intent data) {
	}

	/**
	 * Called when the device configuration changes, this included events like
	 * screen orientation change. See
	 * {@link android.app.Activity#onConfigurationChanged}.
	 */
	public void onConfigurationChanged(Configuration newConfig) {
	}

	public Boolean onContextItemSelected(MenuItem item) {
		return null;
	}

	public void onContextMenuClosed(Menu menu) {
	}

	public void onCreateContextMenu(ContextMenu menu, View v,
			ContextMenuInfo menuInfo) {
	}

	public Boolean onKeyLongPress(int keyCode, KeyEvent event) {
		return null;
	}

	public Boolean onKeyMultiple(int keyCode, int repeatCount, KeyEvent event) {
		return null;
	}

	public Boolean onKeyUp(int keyCode, KeyEvent event) {
		return null;
	}

	public void onLowMemory() {
	}

	public Boolean onSearchRequested() {
		return null;
	}

	public Boolean onTouchEvent(MotionEvent event) {
		return null;
	}

	public Boolean onTrackballEvent(MotionEvent event) {
		return null;
	}

	public void onUserInteraction() {
	}

	public void onWindowAttributesChanged(LayoutParams params) {
	}

	public void onWindowFocusChanged(boolean hasFocus) {
	}

	protected void onPostResume() {
	}

	protected void onResume() {
	}

	protected void onPause() {
	}

	protected void onUserLeaveHint() {
	}

	protected void onSaveInstanceState(Bundle outState) {
	}

	protected void onRestoreInstanceState(Bundle savedInstanceState) {
	}
	
	/**
	 * Called when a reload update is started.
	 */
	protected void onReloadUpdateApply() {
		
	}
	
	/**
	 * Called when a system service is requested. See
	 * {@link android.add.Application#getSystemService}.
	 * @param name
	 */
	public Object getSystemService(final String name) {
		return null;
	}

	/**
	 * Called before the initial page is loaded in the webView. Returning a
	 * value other than nil implies your module has correctly handled this
	 * event.
	 * @param webView
	 */
	public Boolean onLoadInitialPage(final ForgeWebView webView) {
		return null;
	}

	/**
	 * Called on android-23 or later when a permission is requested.
	 */
	public void onRequestPermissionsResult(int requestCode, String permissions[], int[] grantResults) {		
	}

	/**
	 * Called when the soft keyboard has become visible
	 * @param height
	 */
	public void onKeyboardDidShow(float height) {
	}
	
	/**
	 * Called when the soft keyboard has been hidden
	 */
	public void onKeyboardDidHide() {
	}
}