package io.trigger.forge.android.util;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;

import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.PorterDuff.Mode;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.util.DisplayMetrics;

public class BitmapUtil {
	public static Bitmap bitmapFromStream(Context context, InputStream stream, boolean retry) {
		BitmapFactory.Options options = new BitmapFactory.Options();
		options.inPurgeable = true;
		options.inInputShareable = true;

		Bitmap bitmap = null;
		try {
			bitmap = BitmapFactory.decodeStream(stream, null, options);
		} catch (OutOfMemoryError e) {
			// TODO: Try smaller sample size
			System.gc();
			if (retry) {
				return bitmapFromStream(context, stream, false);
			}
		}

		return bitmap;
	}

	public static Bitmap bitmapFromStream(Context context, InputStream stream) {
		return bitmapFromStream(context, stream, true);
	}

	public static Bitmap bitmapFromLocalFile(Context context, String path) throws IOException {
		return bitmapFromStream(context, context.getAssets().open("src/" + path));
	}

	public static Bitmap bitmapFromUri(Context context, Uri file) throws IOException {
		if (file.getScheme().equals("content")) {
			return bitmapFromStream(context, context.getContentResolver().openInputStream(file));
		} else if (file.getScheme().equals("file")) {
			File filepath = new File(file.getPath());
			if (filepath.exists()) {
				return bitmapFromStream(context, new FileInputStream(filepath));
			} else {
				return null;
			}
		} else {
			return null;
		}
	}
	
	public static Drawable drawableFromStream(Context context, InputStream stream) {
		return new BitmapDrawable(context.getResources(), bitmapFromStream(context, stream));
	}

	public static Matrix matrixForBitmap(Context context, Bitmap bitmap, int maxWidth, int maxHeight, int rotation) {
		Matrix matrix = new Matrix();
		float scale = 1.0f;
		if (maxWidth != 0 && maxWidth < bitmap.getWidth()) {
			float newScale = (float) maxWidth / (float) bitmap.getWidth();
			if (scale > newScale) {
				scale = newScale;
			}
		}
		if (maxHeight != 0 && maxHeight < bitmap.getHeight()) {
			float newScale = (float) maxHeight / (float) bitmap.getHeight();
			if (scale > newScale) {
				scale = newScale;
			}
		}
		if (rotation == 90) {
			matrix.setRotate(rotation, bitmap.getHeight() / 2, bitmap.getHeight() / 2);
		} else if (rotation == 180) {
			matrix.setRotate(rotation, bitmap.getWidth() / 2, bitmap.getHeight() / 2);
		} else if (rotation == 270) {
			matrix.setRotate(rotation, bitmap.getWidth() / 2, bitmap.getWidth() / 2);
		}
		matrix.postScale(scale, scale, 0.0f, 0.0f);
		return matrix;
	}

	public static Matrix matrixForBitmap(Context context, Bitmap bitmap, int maxWidth, int maxHeight) {
		return matrixForBitmap(context, bitmap, maxWidth, maxHeight, 0);
	}

	public static Bitmap applyMatrix(Context context, Bitmap bitmap, Matrix matrix) {
		if (matrix.isIdentity()) {
			return bitmap;
		} else {
			try {
				int width = bitmap.getWidth();
				int height = bitmap.getHeight();
				return Bitmap.createBitmap(bitmap, 0, 0, width, height, matrix, true);
			} catch (OutOfMemoryError e) {
				// TODO: Subsample?
				return null;
			} finally {
				bitmap.recycle();
			}
		}
	}
	
	public static Bitmap scaledBitmapFromStream(Context context, InputStream stream,  int maxWidth, int maxHeight) throws IOException {
		Bitmap bitmap = bitmapFromStream(context, stream);

		if (bitmap == null) {
			throw new IOException();
		}

		DisplayMetrics metrics = new DisplayMetrics();
		((Activity) context).getWindowManager().getDefaultDisplay().getMetrics(metrics);

		Matrix matrix = matrixForBitmap(context, bitmap, Math.round(metrics.density * maxWidth), Math.round(metrics.density * maxHeight));

		return applyMatrix(context, bitmap, matrix);
	}

	public static Bitmap scaledBitmapFromLocalFile(Context context, String path, int maxWidth, int maxHeight) throws IOException {
		Bitmap bitmap = bitmapFromLocalFile(context, path);

		if (bitmap == null) {
			throw new IOException();
		}

		DisplayMetrics metrics = new DisplayMetrics();
		((Activity) context).getWindowManager().getDefaultDisplay().getMetrics(metrics);

		Matrix matrix = matrixForBitmap(context, bitmap, Math.round(metrics.density * maxWidth), Math.round(metrics.density * maxHeight));

		return applyMatrix(context, bitmap, matrix);
	}

	public static Drawable scaledDrawableFromLocalFile(Context context, String path, int maxWidth, int maxHeight) throws IOException {
		Bitmap bitmap = scaledBitmapFromLocalFile(context, path, maxWidth, maxHeight);

		return new BitmapDrawable(context.getResources(), bitmap);
	}
	
	public static Drawable scaledDrawableFromStream(Context context, InputStream stream, int maxWidth, int maxHeight) throws IOException {
		return new BitmapDrawable(context.getResources(), scaledBitmapFromStream(context, stream, maxWidth, maxHeight));
	}

	public static Drawable scaledDrawableFromLocalFileWithTint(Context context, String path, int maxWidth, int maxHeight, int tint) throws IOException {
		Bitmap bitmap = scaledBitmapFromLocalFile(context, path, maxWidth, maxHeight);

		Bitmap output = Bitmap.createBitmap(bitmap.getWidth(), bitmap.getHeight(), Bitmap.Config.ARGB_8888);
		Canvas canvas = new Canvas(output);
		canvas.drawBitmap(bitmap.extractAlpha(), 0, 0, new Paint(Paint.ANTI_ALIAS_FLAG));
		canvas.drawColor(tint, Mode.SRC_ATOP);

		bitmap.recycle();

		return new BitmapDrawable(context.getResources(), output);
	}
	
	public static Drawable scaledDrawableFromStreamWithTint(Context context, InputStream stream, int maxWidth, int maxHeight, int tint) throws IOException {
		Bitmap bitmap = scaledBitmapFromStream(context, stream, maxWidth, maxHeight);

		Bitmap output = Bitmap.createBitmap(bitmap.getWidth(), bitmap.getHeight(), Bitmap.Config.ARGB_8888);
		Canvas canvas = new Canvas(output);
		canvas.drawBitmap(bitmap.extractAlpha(), 0, 0, new Paint(Paint.ANTI_ALIAS_FLAG));
		canvas.drawColor(tint, Mode.SRC_ATOP);

		bitmap.recycle();

		return new BitmapDrawable(context.getResources(), output);
	}
}
