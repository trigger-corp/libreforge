#import <Foundation/Foundation.h>
#import <WebKit/WebKit.h>
//#import <UserNotifications/UserNotifications.h>

@interface ForgeEventListener : NSObject

+ (void)applicationDidFinishLaunching:(UIApplication *)application;
+ (NSNumber*)application:(UIApplication *)application willFinishLaunchingWithOptions:(NSDictionary *)launchOptions;
+ (void)applicationDidBecomeActive:(UIApplication *)application;
+ (void)applicationWillResignActive:(UIApplication *)application;
+ (void)applicationDidReceiveMemoryWarning:(UIApplication *)application;
+ (void)applicationWillTerminate:(UIApplication *)application;
+ (void)applicationSignificantTimeChange:(UIApplication *)application;

+ (void)application:(UIApplication *)application willChangeStatusBarOrientation:(UIInterfaceOrientation)newStatusBarOrientation duration:(NSTimeInterval)duration;
+ (void)application:(UIApplication *)application didChangeStatusBarOrientation:(UIInterfaceOrientation)oldStatusBarOrientation;
+ (void)application:(UIApplication *)application willChangeStatusBarFrame:(CGRect)newStatusBarFrame;
+ (void)application:(UIApplication *)application didChangeStatusBarFrame:(CGRect)oldStatusBarFrame;

+ (void)application:(UIApplication *)application didFailToRegisterForRemoteNotificationsWithError:(NSError *)error;

+ (void)applicationProtectedDataWillBecomeUnavailable:(UIApplication *)application;
+ (void)applicationProtectedDataDidBecomeAvailable:(UIApplication *)application;

+ (void)application:(UIApplication *)application preDidFinishLaunchingWithOptions:(NSDictionary *)launchOptions;
+ (void)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions;
+ (void)application:(UIApplication *)application postDidFinishLaunchingWithOptions:(NSDictionary *)launchOptions;
+ (void)application:(UIApplication *)application didRegisterForRemoteNotificationsWithDeviceToken:(NSData *)newDeviceToken;

// deprecated
//+ (void)application:(UIApplication *)application didReceiveRemoteNotification:(NSDictionary *)userInfo;
+ (void)application:(UIApplication *)application didReceiveRemoteNotification:(NSDictionary *)userInfo fetchCompletionHandler:(void (^)(UIBackgroundFetchResult result))completionHandler;

// TODO disable this for now because it forces us to link with UserNotifications.framework
// deprecated
//+ (void)application:(UIApplication *)application handleActionWithIdentifier:(NSString *)identifier forRemoteNotification:(NSDictionary *)userInfo completionHandler:(void (^)(void))completionHandler;
//+ (void)userNotificationCenter:(UNUserNotificationCenter *)center didReceiveNotificationResponse:(UNNotificationResponse *)response withCompletionHandler:(void (^)(void))completionHandler;

+ (void)applicationDidEnterBackground:(UIApplication *)application;
+ (void)applicationWillEnterForeground:(UIApplication *)application;
+ (void)applicationWillResume:(UIApplication *)application;
+ (void)applicationIsReloading;

+ (void)launchImageLoad;
+ (void)preFirstWebViewLoad;
+ (void)firstWebViewLoad;

+ (NSNumber*)onLoadInitialPage;

+ (NSNumber*)application:(UIApplication *)application openURL:(NSURL *)url sourceApplication:(NSString *)sourceApplication annotation:(id)annotation;

+ (NSNumber*)supportedInterfaceOrientations;

+ (NSNumber*)canBecomeFirstResponder;
+ (NSNumber*)canResignFirstResponder;

+ (void)remoteControlReceivedWithEvent:(UIEvent *) receivedEvent;

+ (NSNumber*)prefersStatusBarHidden;
+ (NSNumber*)preferredStatusBarStyle;

+ (void)touchesBegan:(NSSet *)touches withEvent:(UIEvent *)event;
+ (void)touchesCancelled:(NSSet *)touches withEvent:(UIEvent *)event;
+ (void)touchesEnded:(NSSet *)touches withEvent:(UIEvent *)event;
+ (void)touchesMoved:(NSSet *)touches withEvent:(UIEvent *)event;

+ (void)willTransitionToTraitCollection:(UITraitCollection *)newCollection
			  withTransitionCoordinator:(id<UIViewControllerTransitionCoordinator>)coordinator;
+ (void)viewWillTransitionToSize:(CGSize)size
	   withTransitionCoordinator:(id<UIViewControllerTransitionCoordinator>)coordinator;

+ (void)keyboardWillShow:(NSNotification*)notification;
+ (void)keyboardWillHide:(NSNotification*)notification;
+ (void)keyboardDidShow:(NSNotification*)notification;
+ (void)keyboardDidHide:(NSNotification*)notification;

+ (void)applicationWillConfigureWebView:(WKWebViewConfiguration*)configuration;

// deprecated
+ (NSNumber*)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)interfaceOrientation;
+ (void)willRotateToInterfaceOrientation:(UIInterfaceOrientation)toInterfaceOrientation duration:(NSTimeInterval)duration;
+ (void)didRotateFromInterfaceOrientation:(UIInterfaceOrientation)fromInterfaceOrientation;

@end
