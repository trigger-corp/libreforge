package io.trigger.forge.android.core;

import android.webkit.MimeTypeMap;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.List;

/**
 * A collection of useful functions
 */
public class ForgeUtil {
	public static boolean urlMatchesPattern(String url, String pattern) {
		try {
			URI parsed = new URI(url);
			if (pattern.equals("<all_urls>")) {
				return true;
			}
			
			// Check scheme
			String patternScheme = pattern.split("://")[0];
			if (!patternScheme.equals("*") && !patternScheme.equals(parsed.getScheme())) {
				return false;
			}
			
			// Check host
			String patternHostPath = pattern.split("://")[1];
			String patternHost = patternHostPath.split("/")[0];
			if (!patternHost.equals("*")) {
				if (patternHost.startsWith("*.")) {
					if (!parsed.getHost().endsWith("."+patternHost.substring(2)) && !patternHost.substring(2).equals(parsed.getHost())) {
						return false;
					}
				} else {
					if (!patternHost.equals(parsed.getHost()) && !(parsed.getHost() == null && patternHost.equals(""))) {
						return false;
					}
				}
			}			
			
			// Check path
			String patternPath = patternHostPath.substring(patternHost.length()).replace("*", ".*");
			if (patternPath.length() > 0) {
				if (!parsed.getPath().matches(patternPath)) {
					return false;
				}
			}
			return true;
		} catch (URISyntaxException e) {
			return false;
		}
	}

    public static String[] normaliseMimeTypes(String mimeTypes) {
        if (mimeTypes == null) {
            return new String[] {"*/*"};
        }

        final String[] mimeTypesArray = mimeTypes.split(",");
        final List<String> computedMimeTypes = new ArrayList<>();
        final MimeTypeMap mimeMap = MimeTypeMap.getSingleton();

        // Get mime type for file extension
        for (int i=0; i < mimeTypesArray.length; ++i) {
            final String mimeType = mimeTypesArray[i];
            if (mimeType.startsWith(".")) {
                final String fileExtensionMime = mimeMap.getMimeTypeFromExtension(mimeType.substring(1));
                if (fileExtensionMime != null) {
                    computedMimeTypes.add(fileExtensionMime);
                }
            } else if (mimeMap.hasMimeType(mimeType)) {
                computedMimeTypes.add(mimeType);
            }
        }

        if (computedMimeTypes.size() == 0) {
            // We show all file types if the mime types are not supported so user has a choice to select a file
            return new String[] {"*/*"};
        }

        return computedMimeTypes.toArray(new String[computedMimeTypes.size()]);
    }
}