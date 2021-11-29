#import "ForgeAppDelegate.h"
#import "WKWebViewController.h"
#import "BorderControl.h"
#import "ForgeLog.h"
#import "ForgeApp.h"

#import "NSFileManager+DoNotBackup.h"

#import <objc/objc.h>
#import <objc/runtime.h>

//#import <UserNotifications/UserNotifications.h>

#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wundeclared-selector"

@implementation ForgeAppDelegate

@synthesize window = _window;
@synthesize viewController = _viewController;

- (id)init {
    self = [super init];
    [ForgeApp.sharedApp setAppDelegate:self];

    NSMutableSet *enabledModules = [[NSMutableSet alloc] init];

    // Required modules
    [enabledModules addObject:@"internal"];
    [enabledModules addObject:@"logging"];
    [enabledModules addObject:@"event"];
    if ([ForgeApp.sharedApp flag:@"ios_disable_httpd"] != YES) {
        [enabledModules addObject:@"httpd"];
    }
    [enabledModules addObject:@"tools"];
    [enabledModules addObject:@"reload"];
    [enabledModules addObject:@"live"];
    [enabledModules addObject:@"native"];
    [enabledModules addObject:@"layout"];

    NSDictionary *modules = ForgeApp.sharedApp.moduleMapping;
    if (modules != nil) {
        [enabledModules addObjectsFromArray:[modules allKeys]];
    }

    //NSString *appName = [[NSBundle mainBundle] objectForInfoDictionaryKey:@"CFBundleName"];
    NSString *appName = @"ForgeInspector"; // We need to use the original bundle name

    for (NSString *module in enabledModules) {
        NSLog(@"Initializing module: %@", module);
        // Event listener
        Class moduleEventListener = NSClassFromString([NSString stringWithFormat:@"%@_EventListener", module]);
        if (!moduleEventListener) { /* try swift */
            //NSLog(@"Trying swift event listeners for: %@", module);
            moduleEventListener = NSClassFromString([NSString stringWithFormat:@"%@.%@_EventListener", appName, module]);
        }
        if (moduleEventListener) {
            NSLog(@"\tAdded event listener(s) for %@", module);
            [ForgeApp.sharedApp.eventListeners addObject:moduleEventListener];
        }

        // API Methods
        NSString *moduleAPI = [NSString stringWithFormat:@"%@_API", module];
        unsigned int methodCount;
        Method *methods = class_copyMethodList(object_getClass(NSClassFromString(moduleAPI)), &methodCount);
        if (methodCount == 0) { /* try swift */
            //NSString *classStringName = [NSString stringWithFormat:@"_TtC%d%@%d%@", appName.length, appName, className.length, className];
            moduleAPI = [NSString stringWithFormat:@"%@.%@_API", appName, module];
            methods = class_copyMethodList(object_getClass(NSClassFromString(moduleAPI)), &methodCount);
            if (methodCount == 0) {
                [ForgeLog d:[NSString stringWithFormat:@"No methods found for module: %@", module]];
            }
        }
        for (int i = 0; i < methodCount; i++) {
            SEL name = method_getName(methods[i]);
            NSString *selector = NSStringFromSelector(name);
            NSString *selectorPrefix = [selector substringToIndex:[selector rangeOfString:@":"].location];
            if ([selectorPrefix hasPrefix:@"_"]) {
                NSLog(@"\tSkipping private method: %@.%@", module, selectorPrefix);
                continue;
            }
            NSString *jsMethod = [NSString stringWithFormat:@"%@.%@", module, selectorPrefix];
            [BorderControl addAPIMethod:jsMethod withClass:moduleAPI andSelector:selector];
            NSLog(@"\tAdded method: %@", jsMethod);
        }
        free(methods);

        if ([module isEqualToString:@"inspector"]) {
            // Enable extra inspector events for debugging.
            [ForgeApp.sharedApp setInspectorEnabled:YES];
        }
    }
    return self;
}

+ (void)check_disable_web_storage_backup {
    // Mark localstorage to not be backed up by icloud if needed
    BOOL disable_web_storage_backup = false;
    if ([[[ForgeApp.sharedApp.appConfig objectForKey:@"core"] objectForKey:@"ios"] objectForKey:@"disable_web_storage_backup"] != nil) {
        disable_web_storage_backup = [[[[ForgeApp.sharedApp.appConfig objectForKey:@"core"] objectForKey:@"ios"] objectForKey:@"disable_web_storage_backup"] boolValue];
    }
    if (disable_web_storage_backup) {
        NSURL *webkitDir = [ForgeApp.sharedApp.applicationSupportDirectory URLByAppendingPathComponent:@"webkit"];
        NSURL *localStorage = [webkitDir URLByAppendingPathComponent:@"file__0.localstorage"];
        NSURL *webSQLMainDB = [webkitDir URLByAppendingPathComponent:@"Databases.db"];
        NSURL *webSQLDatabases = [webkitDir URLByAppendingPathComponent:@"file__0"];
        if ([[NSFileManager defaultManager] fileExistsAtPath: [localStorage path]]) {
            NSLog(@"Disabling iCloud backup for LocalStorage");
            [[NSFileManager defaultManager] addSkipBackupAttributeToItemAtURL:localStorage];
        }
        if ([[NSFileManager defaultManager] fileExistsAtPath: [webSQLMainDB path]]) {
            NSLog(@"Disabling iCloud backup for WebSQLMainDB");
            [[NSFileManager defaultManager] addSkipBackupAttributeToItemAtURL:webSQLMainDB];
        }
        if ([[NSFileManager defaultManager] fileExistsAtPath: [webSQLDatabases path]]) {
            NSLog(@"Disabling iCloud backup for WebSQLDatabases");
            [[NSFileManager defaultManager] addSkipBackupAttributeToItemAtURL:webSQLDatabases];
        }
    }
}

- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    [ForgeApp.sharedApp nativeEvent:@selector(application:preDidFinishLaunchingWithOptions:) withArgs:@[application ? application : [NSNull null], launchOptions ? launchOptions : [NSNull null]]];

    // Set localstorage and websql locations so they are not in the temporary cache folder
    NSUserDefaults *prefs = [NSUserDefaults standardUserDefaults];
    NSURL *webkitDir = [ForgeApp.sharedApp.applicationSupportDirectory URLByAppendingPathComponent:@"webkit"];
    [prefs setObject:[webkitDir path] forKey:@"WebDatabaseDirectory"];
    [prefs setObject:[webkitDir path] forKey:@"WebKitLocalStorageDatabasePathPreferenceKey"];
    [prefs setInteger:1 forKey:@"WebKitCacheModelPreferenceKey"];
    [prefs removeObjectForKey:@"WebKitStandardFont"];
    [prefs synchronize];

    // Mark localstorage to not be backed up by icloud if needed
    [ForgeAppDelegate check_disable_web_storage_backup];

    self.window = [[UIWindow alloc] initWithFrame:[[UIScreen mainScreen] bounds]];

    // Create and initialize webview controller
    self.viewController = [[WKWebViewController alloc] initWithNibName:@"WKWebViewController" bundle:[NSBundle bundleWithPath:[[[NSBundle mainBundle] resourcePath] stringByAppendingPathComponent:@"ForgeCore.bundle"]]];
    [ForgeApp.sharedApp setViewController:self.viewController];
    self.window.rootViewController = self.viewController;
    if (self.viewController.view == nil) {
        NSLog(@"Force lazy loading of nib");
    }

    application.statusBarStyle = self.viewController.statusBarStyle;

    [ForgeApp.sharedApp nativeEvent:@selector(application:didFinishLaunchingWithOptions:) withArgs:@[application ? application : [NSNull null], launchOptions ? launchOptions : [NSNull null]]];

    [self.window makeKeyAndVisible];

    [ForgeApp.sharedApp nativeEvent:@selector(application:postDidFinishLaunchingWithOptions:) withArgs:@[application ? application : [NSNull null], launchOptions ? launchOptions : [NSNull null]]];

    [ForgeApp.sharedApp nativeEvent:@selector(launchImageLoad) withArgs:@[]];

    return YES;
}

- (void)touchesBegan:(NSSet *)touches withEvent:(UIEvent *)event {
    [super touchesBegan:touches withEvent:event];
    [ForgeApp.sharedApp nativeEvent:@selector(touchesBegan:withEvent:) withArgs:@[touches	? touches : [NSNull null], event ? event : [NSNull null]]];
}

- (void)touchesCancelled:(NSSet *)touches withEvent:(UIEvent *)event {
    [super touchesCancelled:touches withEvent:event];
    [ForgeApp.sharedApp nativeEvent:@selector(touchesCancelled:withEvent:) withArgs:@[touches	? touches : [NSNull null], event ? event : [NSNull null]]];
}

- (void)touchesEnded:(NSSet *)touches withEvent:(UIEvent *)event {
    [super touchesEnded:touches withEvent:event];
    [ForgeApp.sharedApp nativeEvent:@selector(touchesEnded:withEvent:) withArgs:@[touches	? touches : [NSNull null], event ? event : [NSNull null]]];
}

- (void)touchesMoved:(NSSet *)touches withEvent:(UIEvent *)event {
    [super touchesMoved:touches withEvent:event];
    [ForgeApp.sharedApp nativeEvent:@selector(touchesMoved:withEvent:) withArgs:@[touches	? touches : [NSNull null], event ? event : [NSNull null]]];
}

- (void)application:(UIApplication *)application didRegisterForRemoteNotificationsWithDeviceToken:(NSData *)newDeviceToken {
    [ForgeApp.sharedApp nativeEvent:@selector(application:didRegisterForRemoteNotificationsWithDeviceToken:) withArgs:@[application ? application : [NSNull null], newDeviceToken ? newDeviceToken : [NSNull null]]];
}

// DEPRECATED
/*- (void)application:(UIApplication *)application didReceiveRemoteNotification:(NSDictionary *)userInfo {
    [[ForgeApp sharedApp] nativeEvent:@selector(application:didReceiveRemoteNotification:) withArgs:@[application ? application : [NSNull null], userInfo ? userInfo : [NSNull null]]];
}*/

- (void)application:(UIApplication *)application didReceiveRemoteNotification:(NSDictionary *)userInfo fetchCompletionHandler:(void (^)(UIBackgroundFetchResult result))completionHandler {
    [[ForgeApp sharedApp] nativeEvent:@selector(application:didReceiveRemoteNotification:fetchCompletionHandler:) withArgs:@[application ? application : [NSNull null], userInfo ? userInfo : [NSNull null], completionHandler ? completionHandler : ^(UIBackgroundFetchResult result){ }]];
}

// DEPRECATED
/*- (void)application:(UIApplication *)application handleActionWithIdentifier:(NSString *)identifier forRemoteNotification:(NSDictionary *)userInfo completionHandler:(void (^)(void))completionHandler {
    [[ForgeApp sharedApp] nativeEvent:@selector(application:handleActionWithIdentifier:forRemoteNotification:completionHandler:) withArgs:@[application ? application : [NSNull null], identifier ? identifier : [NSNull null], userInfo ? userInfo : [NSNull null], completionHandler ? completionHandler : ^{ }]];
}*/

// TODO disable this for now because it forces us to link with UserNotifications.framework
/*- (void)userNotificationCenter:(UNUserNotificationCenter *)center didReceiveNotificationResponse:(UNNotificationResponse *)response withCompletionHandler:(void (^)(void))completionHandler {
    [[ForgeApp sharedApp] nativeEvent:@selector(application:handleActionWithIdentifier:didReceiveNotificationResponse:withCompletionHandler:) withArgs:@[center ? center : [NSNull null], response ? response : [NSNull null], completionHandler ? completionHandler : ^{ }]];
}*/

- (void)applicationDidEnterBackground:(UIApplication *)application {
    [ForgeApp.sharedApp nativeEvent:@selector(applicationDidEnterBackground:) withArgs:@[application ? application : [NSNull null]]];

    // Mark localstorage to not be backed up by icloud if needed
    [ForgeAppDelegate check_disable_web_storage_backup];
}

- (void)applicationWillEnterForeground:(UIApplication *)application {
    [ForgeApp.sharedApp nativeEvent:@selector(applicationWillEnterForeground:) withArgs:@[application ? application : [NSNull null]]];
}

- (BOOL)application:(UIApplication *)application openURL:(NSURL *)url options:(NSDictionary<UIApplicationOpenURLOptionsKey, id> *)options {
    NSString *sourceApplication = options[UIApplicationOpenURLOptionsSourceApplicationKey];
    id annotation = options[UIApplicationOpenURLOptionsSourceApplicationKey];

    return ((NSNumber*)[ForgeApp.sharedApp
                        nativeEvent:@selector(application:openURL:sourceApplication:annotation:) withArgs:@[application ? application : [NSNull null], url ? url : [NSNull null], sourceApplication ? sourceApplication : [NSNull null], annotation ? annotation : [NSNull null]]]).boolValue;
}

- (void)applicationDidFinishLaunching:(UIApplication *)application {
    [ForgeApp.sharedApp nativeEvent:@selector(applicationDidFinishLaunching:) withArgs:@[application ? application : [NSNull null]]];
}

- (BOOL)application:(UIApplication *)application willFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    return ((NSNumber*)[ForgeApp.sharedApp nativeEvent:@selector(application:willFinishLaunchingWithOptions:) withArgs:@[application ? application : [NSNull null], launchOptions ? launchOptions : [NSNull null]]]).boolValue;
}

- (void)applicationDidBecomeActive:(UIApplication *)application {
    [ForgeApp.sharedApp nativeEvent:@selector(applicationDidBecomeActive:) withArgs:@[application ? application : [NSNull null]]];
}
- (void)applicationWillResignActive:(UIApplication *)application {
    [ForgeApp.sharedApp nativeEvent:@selector(applicationWillResignActive:) withArgs:@[application ? application : [NSNull null]]];
}
- (void)applicationDidReceiveMemoryWarning:(UIApplication *)application {
    [ForgeApp.sharedApp nativeEvent:@selector(applicationDidReceiveMemoryWarning:) withArgs:@[application ? application : [NSNull null]]];
}
- (void)applicationWillTerminate:(UIApplication *)application {
    [ForgeApp.sharedApp nativeEvent:@selector(applicationWillTerminate:) withArgs:@[application ? application : [NSNull null]]];
}
- (void)applicationSignificantTimeChange:(UIApplication *)application {
    [ForgeApp.sharedApp nativeEvent:@selector(applicationSignificantTimeChange:) withArgs:@[application ? application : [NSNull null]]];
}
- (void)application:(UIApplication *)application willChangeStatusBarOrientation:(UIInterfaceOrientation)newStatusBarOrientation duration:(NSTimeInterval)duration {
    [ForgeApp.sharedApp nativeEvent:@selector(application:willChangeStatusBarOrientation:duration:) withArgs:@[application ? application : [NSNull null], [NSNumber numberWithInt:(int)newStatusBarOrientation], [NSNumber numberWithInt:duration]]];
}
- (void)application:(UIApplication *)application didChangeStatusBarOrientation:(UIInterfaceOrientation)oldStatusBarOrientation {
    [ForgeApp.sharedApp nativeEvent:@selector(application:didChangeStatusBarOrientation:) withArgs:@[application ? application : [NSNull null], [NSNumber numberWithInt:(int)oldStatusBarOrientation]]];
}
- (void)application:(UIApplication *)application willChangeStatusBarFrame:(CGRect)newStatusBarFrame {
    [ForgeApp.sharedApp nativeEvent:@selector(application:willChangeStatusBarFrame:) withArgs:@[application ? application : [NSNull null], [NSValue valueWithCGRect:newStatusBarFrame]]];
}
- (void)application:(UIApplication *)application didChangeStatusBarFrame:(CGRect)oldStatusBarFrame {
    [ForgeApp.sharedApp nativeEvent:@selector(application:didChangeStatusBarFrame:) withArgs:@[application ? application : [NSNull null], [NSValue valueWithCGRect:oldStatusBarFrame]]];
}
- (void)application:(UIApplication *)application didFailToRegisterForRemoteNotificationsWithError:(NSError *)error {
    [ForgeApp.sharedApp nativeEvent:@selector(application:didFailToRegisterForRemoteNotificationsWithError:) withArgs:@[application ? application : [NSNull null], error ? error : [NSNull null]]];

}
- (void)applicationProtectedDataWillBecomeUnavailable:(UIApplication *)application {
    [ForgeApp.sharedApp nativeEvent:@selector(applicationProtectedDataWillBecomeUnavailable:) withArgs:@[application ? application : [NSNull null]]];
}
- (void)applicationProtectedDataDidBecomeAvailable:(UIApplication *)application {
    [ForgeApp.sharedApp nativeEvent:@selector(applicationProtectedDataDidBecomeAvailable:) withArgs:@[application ? application : [NSNull null]]];
}
- (void)remoteControlReceivedWithEvent:(UIEvent *) receivedEvent {
    [ForgeApp.sharedApp nativeEvent:@selector(remoteControlReceivedWithEvent:) withArgs:@[receivedEvent ? receivedEvent : [NSNull null]]];
}

@end

#pragma clang diagnostic pop
