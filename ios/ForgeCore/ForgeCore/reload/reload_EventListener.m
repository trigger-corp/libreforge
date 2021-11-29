#import "reload_EventListener.h"
#import "reload_Util.h"
#import "ForgeLog.h"
#import "ForgeApp.h"
#import "WKWebViewController.h"

@implementation reload_EventListener

+ (void)application:(UIApplication *)application preDidFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
	NSUserDefaults *prefs = [NSUserDefaults standardUserDefaults];
	// Install id
	if ([prefs objectForKey:@"reload-install-id"] == nil) {
		NSString *uuid = (__bridge_transfer NSString *)CFUUIDCreateString(kCFAllocatorDefault, CFUUIDCreate(kCFAllocatorDefault));
		[prefs setValue:uuid forKey:@"reload-install-id"];
	}

	// UUID to put assets in - workaround for iOS 6 caching issues
	if ([prefs objectForKey:@"reload-assets-id"] == nil) {
		NSString *uuid = (__bridge_transfer NSString *)CFUUIDCreateString(kCFAllocatorDefault, CFUUIDCreate(kCFAllocatorDefault));
		[prefs setValue:uuid forKey:@"reload-assets-id"];
	}

	NSURL *applicationSupportDirectory = ForgeApp.sharedApp.applicationSupportDirectory;
	NSString *versionCode = [[NSBundle mainBundle] objectForInfoDictionaryKey:@"CFBundleVersion"];
	if (![versionCode isEqualToString:[prefs objectForKey:@"reload-version-code"]]) {
		// New version, clear any reload updates
		[ForgeLog i:@"New app version, removing any reload update files."];
		NSURL *updateDir = [applicationSupportDirectory URLByAppendingPathComponent:@"update"];
		NSURL *liveDir = [applicationSupportDirectory URLByAppendingPathComponent:@"live"];
		[[NSFileManager defaultManager] removeItemAtURL:updateDir error:nil];
		[[NSFileManager defaultManager] removeItemAtURL:liveDir error:nil];

		// Delete the current assets folder
        NSURL *assetsFolder = [ForgeApp.sharedApp assetsFolderLocationWithPrefs:prefs];
		[[NSFileManager defaultManager] removeItemAtURL:assetsFolder error:nil];

		// Use a new assets folder when recreating symlinks to avoid caching
		NSString *uuid = (__bridge_transfer NSString *)CFUUIDCreateString(kCFAllocatorDefault, CFUUIDCreate(kCFAllocatorDefault));
		[prefs setValue:uuid forKey:@"reload-assets-id"];
	}
	[prefs setValue:versionCode forKey:@"reload-version-code"];
	[prefs synchronize];

    NSURL *updatePath = [applicationSupportDirectory URLByAppendingPathComponent:@"update/state"];;
    if ([[NSFileManager defaultManager] fileExistsAtPath:[updatePath path]]) {
        // Update in some state - find out what
        NSString *state = [reload_Util getUpdateState];
        if ([state hasPrefix:@"complete"] && ![reload_Util reloadManual]) {
            // Completed update, apply now
            [reload_Util applyUpdate:nil];
        }
    }
	// Try to update now - in background
	if ([reload_Util reloadEnabled] && ![reload_Util reloadManual]) {
		dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_LOW, 0), ^{
			if ([reload_Util updateAvailable]) {
				[reload_Util updateWithLock:nil];
			}
		});
	}
}

+ (void)applicationDidEnterBackground:(UIApplication *)application {

	// Check for an update in the background whenever the app loses focus.
	if ([reload_Util reloadEnabled] && ![reload_Util reloadManual]) {
		UIBackgroundTaskIdentifier __block bgTask = [application beginBackgroundTaskWithExpirationHandler:^{
			[application endBackgroundTask:bgTask];
			bgTask = UIBackgroundTaskInvalid;
		}];

		dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_LOW, 0), ^{
			if ([reload_Util updateAvailable]) {
				[reload_Util updateWithLock:nil];
			}

			[application endBackgroundTask:bgTask];
			bgTask = UIBackgroundTaskInvalid;
		});
	}
}

+ (void)applicationWillEnterForeground:(UIApplication *)application {
    NSURL *updatePath = [ForgeApp.sharedApp.applicationSupportDirectory URLByAppendingPathComponent:@"update/state"];
    if ([[NSFileManager defaultManager] fileExistsAtPath:[updatePath path]]) {
        // Update in some state - find out what
        NSString *state = [reload_Util getUpdateState];
        if ([state hasPrefix:@"complete"] && ![reload_Util reloadManual]) {
			// Apply update and reload initial page
			dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_HIGH, 0), ^{
				[reload_Util applyUpdate:nil];
				[ForgeApp.sharedApp.viewController loadInitialPage];
			});

			return;
        }
    }
	// No update applied, we're resuming.
	[ForgeApp.sharedApp nativeEvent:@selector(applicationWillResume:) withArgs:@[application ? application : [NSNull null]]];
}

@end
