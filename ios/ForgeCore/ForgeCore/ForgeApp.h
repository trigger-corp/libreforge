#import <Foundation/Foundation.h>
#import <WebKit/WebKit.h>

#import <ForgeCore/ForgeAppDelegate.h>

@interface ForgeApp : NSObject {
    //int hideStatusCount;
}

// Main webView used for Forge
@property WKWebView* webView;

// appConfig dictionary
@property NSDictionary* appConfig;
@property NSDictionary* moduleMapping;

// Forge app delegate
@property ForgeAppDelegate* appDelegate;

// Forge view controller
@property ForgeViewController* viewController;
@property NSMutableArray* eventListeners;

// Whether the inspector module is enabled - used to enable extra debug events
@property BOOL inspectorEnabled;

+ (ForgeApp*)sharedApp;

- (id)nativeEvent:(SEL)selector withArgs:(NSArray*)args;
- (void)event:(NSString*)name withParam:(id)params;

- (NSDictionary*)configForModule:(NSString*)name;
- (NSDictionary*)configForPlugin:(NSString*)name;
- (NSURL*)bundleLocationRelativeToAssets;

// TODO these need to be private to ForgeCore
- (NSURL*)applicationSupportDirectory;
- (NSURL*)assetsFolderLocationWithPrefs:(NSUserDefaults*)prefs;

- (BOOL)flag:(NSString*)name;

@end
