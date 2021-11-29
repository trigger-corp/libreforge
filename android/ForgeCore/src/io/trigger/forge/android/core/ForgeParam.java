package io.trigger.forge.android.core;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Used on Forge API method parameters to determine what Javascript parameters will be passed to each Java parameter.
 * 
 * <br><br>Example: <code>public static void show(final ForgeTask task, @ForgeParam("text") final String text)</code> will pass the <code>text</code> parameter through from Javascript to Java.
 */
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.PARAMETER)
public @interface ForgeParam {
	public String value();
}
