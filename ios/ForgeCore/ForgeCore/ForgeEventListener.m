#import "ForgeEventListener.h"

/** Modules can extend this class and override methods to implement event listeners. */
@implementation ForgeEventListener

// All event listener methods must be declared here, return values will be used if no module overrides.


/// Pass through from UIApplicationDelegate
+ (void)applicationDidFinishLaunching:(UIApplication *)application {

}

/// Pass through from UIApplicationDelegate
/// @warning Returning a value other than nil implies your module has correctly handled this event.
+ (NSNumber*)application:(UIApplication *)application willFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
	return @NO;
}

/// Pass through from UIApplicationDelegate
+ (void)applicationDidBecomeActive:(UIApplication *)application {

}

/// Pass through from UIApplicationDelegate
+ (void)applicationWillResignActive:(UIApplication *)application {

}

/// Pass through from UIApplicationDelegate
+ (void)applicationDidReceiveMemoryWarning:(UIApplication *)application {

}

/// Pass through from UIApplicationDelegate
+ (void)applicationWillTerminate:(UIApplication *)application {

}

/// Pass through from UIApplicationDelegate
+ (void)applicationSignificantTimeChange:(UIApplication *)application {

}

/// Pass through from UIApplicationDelegate
+ (void)application:(UIApplication *)application willChangeStatusBarOrientation:(UIInterfaceOrientation)newStatusBarOrientation duration:(NSTimeInterval)duration {

}

/// Pass through from UIApplicationDelegate
+ (void)application:(UIApplication *)application didChangeStatusBarOrientation:(UIInterfaceOrientation)oldStatusBarOrientation{

}

// Pass through from UIApplicationDelegate
+ (void)application:(UIApplication *)application willChangeStatusBarFrame:(CGRect)newStatusBarFrame {

}

// Pass through from UIApplicationDelegate
+ (void)application:(UIApplication *)application didChangeStatusBarFrame:(CGRect)oldStatusBarFrame {

}

/// Pass through from UIApplicationDelegate
+ (void)application:(UIApplication *)application didFailToRegisterForRemoteNotificationsWithError:(NSError *)error {

}

/// Pass through from UIApplicationDelegate
+ (void)applicationProtectedDataWillBecomeUnavailable:(UIApplication *)application {

}

/// Pass through from UIApplicationDelegate
+ (void)applicationProtectedDataDidBecomeAvailable:(UIApplication *)application {

}

/// Called at the start of application:didFinishLaunchingWithOptions:, before the webView is created.
+ (void)application:(UIApplication *)application preDidFinishLaunchingWithOptions:(NSDictionary *)launchOptions {

}

/// Called at the end of application:didFinishLaunchingWithOptions:
+ (void)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {

}

/// Called at the end of application:didFinishLaunchingWithOptions:, after the app window is created.
+ (void)application:(UIApplication *)application postDidFinishLaunchingWithOptions:(NSDictionary *)launchOptions {

}

/// Called on application:didRegisterForRemoteNotificationsWithDeviceToken:
+ (void)application:(UIApplication *)application didRegisterForRemoteNotificationsWithDeviceToken:(NSData *)newDeviceToken {

}

// deprecated
//+ (void)application:(UIApplication *)application didReceiveRemoteNotification:(NSDictionary *)userInfo;

/// Called on application:didReceiveRemoteNotification
+ (void)application:(UIApplication *)application didReceiveRemoteNotification:(NSDictionary *)userInfo fetchCompletionHandler:(void (^)(UIBackgroundFetchResult result))completionHandler {
    if (completionHandler) {
        completionHandler(UIBackgroundFetchResultNoData);
    }
}

// TODO disable this for now because it forces us to link with UserNotifications.framework
// deprecated
//+ (void)application:(UIApplication *)application handleActionWithIdentifier:(NSString *)identifier forRemoteNotification:(NSDictionary *)userInfo completionHandler:(void (^)(void))completionHandler;

/// Called on usernotificationCenter:didReceiveNotificationResponse
/*+ (void)userNotificationCenter:(UNUserNotificationCenter *)center didReceiveNotificationResponse:(UNNotificationResponse *)response withCompletionHandler:(void (^)(void))completionHandler {

}*/

/// Called on applicationDidEnterBackground:
+ (void)applicationDidEnterBackground:(UIApplication *)application {

}

/// Called on applicationWillEnterForeground:
+ (void)applicationWillEnterForeground:(UIApplication *)application {

}

/// Called during applicationWillEnterForeground when no reload update has been applied (i.e. application will resume as it was left)
+ (void)applicationWillResume:(UIApplication *)application {

}

/// Called when a reload update is being applied (i.e. when it is no longer safe to use the webview)
+ (void)applicationIsReloading {

}

+ (void)launchImageLoad {

}

/// Called before the initial page is loaded in the webView
/// @warning deprecated in favor of onLoadInitialPage
+ (void)preFirstWebViewLoad {

}

/// Called once the initial page has been loaded
+ (void)firstWebViewLoad {

}

/// Called before the initial page is loaded in the webView
/// @warning Returning a value other than nil implies your module
/// has correctly handled this event.
+ (NSNumber*)onLoadInitialPage {
	return @NO;
}

/// Called on application:openURL:sourceApplication:annotation:
/// @warning Returning a value other than nil implies your module has correctly handled this event.
+ (NSNumber*)application:(UIApplication *)application openURL:(NSURL *)url sourceApplication:(NSString *)sourceApplication annotation:(id)annotation {
	return @NO;
}

/// Called on supportedInterfaceOrientations
/// @warning Returning a value other than nil implies your module has correctly handled this event.
+ (NSNumber*)supportedInterfaceOrientations {
    return [NSNumber numberWithInt:UIInterfaceOrientationMaskAll];
}

/// Called on canBecomeFirstResponder
/// @warning Returning a value other than nil implies your module has correctly handled this event.
+ (NSNumber*)canBecomeFirstResponder {
	return @NO;
}

/// Called on canResignFirstResponder
/// @warning Returning a value other than nil implies your module has correctly handled this event.
+ (NSNumber*)canResignFirstResponder {
	return @NO;
}

/// Called on remoteControlReceivedWithEvent
/// @warning Returning a value other than nil implies your module has correctly handled this event.
+ (void)remoteControlReceivedWithEvent:(UIEvent *) receivedEvent {

}

+ (NSNumber*)prefersStatusBarHidden {
	return nil;
}

+ (NSNumber*)preferredStatusBarStyle {
	return nil;
}

+ (void)touchesBegan:(NSSet *)touches withEvent:(UIEvent *)event {
}

+ (void)touchesCancelled:(NSSet *)touches withEvent:(UIEvent *)event {
}

+ (void)touchesEnded:(NSSet *)touches withEvent:(UIEvent *)event {
}

+ (void)touchesMoved:(NSSet *)touches withEvent:(UIEvent *)event {
}

// Called before split view transition & rotations
+ (void)willTransitionToTraitCollection:(UITraitCollection *)newCollection
			  withTransitionCoordinator:(id<UIViewControllerTransitionCoordinator>)coordinator {
}

// Called after split view transition & rotations
+ (void)viewWillTransitionToSize:(CGSize)size
	   withTransitionCoordinator:(id<UIViewControllerTransitionCoordinator>)coordinator {
}

/// Called on shouldAutorotateToInterfaceOrientation:
/// @warning Returning a value other than nil implies your module has correctly handled this event.
/// @warning Deprecated in favor of: viewWillTransitionToSize
+ (NSNumber*)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)interfaceOrientation {
    return @YES;
}

/// Called on willRotateToInterfaceOrientation:duration:
/// @warning Returning a value other than nil implies your module has correctly handled this event.
/// @warning Deprecated in favor of: viewWillTransitionToSize
+ (void)willRotateToInterfaceOrientation:(UIInterfaceOrientation)toInterfaceOrientation duration:(NSTimeInterval)duration {

}

/// Called on didRotateFromInterfaceOrientation:fromInterfaceOrientation:
/// @warning Returning a value other than nil implies your module has correctly handled this event.
/// @warning Deprecated in favor of: viewWillTransitionToSize
+ (void)didRotateFromInterfaceOrientation:(UIInterfaceOrientation)fromInterfaceOrientation {

}

+ (void)keyboardWillShow:(NSNotification*)notification {
}

+ (void)keyboardWillHide:(NSNotification*)notification {
}

+ (void)keyboardDidShow:(NSNotification*)notification {
}

+ (void)keyboardDidHide:(NSNotification*)notification {
}

+ (void)applicationWillConfigureWebView:(WKWebViewConfiguration*)configuration {
}


@end
