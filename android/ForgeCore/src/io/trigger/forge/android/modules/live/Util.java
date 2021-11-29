package io.trigger.forge.android.modules.live;

import io.trigger.forge.android.core.ForgeApp;
import android.annotation.SuppressLint;
import android.content.Intent;
import android.os.Build;

public class Util {
	@SuppressLint("NewApi")
	static void restartActivity() {
		ForgeApp.getActivity().runOnUiThread(new Runnable() {
			public void run() {
				if (Build.VERSION.SDK_INT >= 11) {
					ForgeApp.getActivity().recreate();
				} else {
					Intent intent = ForgeApp.getActivity().getIntent();
					intent.addFlags(Intent.FLAG_ACTIVITY_NO_ANIMATION);
					ForgeApp.getActivity().finish();
					ForgeApp.getActivity().overridePendingTransition(0, 0);
					ForgeApp.getActivity().startActivity(intent);
					ForgeApp.getActivity().overridePendingTransition(0, 0);
				}
			}
		});
	}
}
