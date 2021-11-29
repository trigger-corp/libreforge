#import <Foundation/Foundation.h>
#import "ForgeAppDelegate.h"

@interface ForgeApp : NSObject {

}

/// Main webView used for Forge
@property WebView* webView;
/// appConfig dictionary
@property NSDictionary* appConfig;
/// Forge app delegate
@property ForgeAppDelegate* appDelegate;
/// Whether the inspector module is enabled - used to enable extra debug events
@property BOOL inspectorEnabled;

@property NSMutableArray* eventListeners;
@property NSMutableDictionary* storedAPIMethods;

+ (ForgeApp*)sharedApp;
- (void)event:(NSString*)name withParam:(id)params;
- (void)callNativeFromJavaScript:(NSString *)callid :(NSString *)method :(NSString *)params;
- (void)returnResult:(NSDictionary*)returnObj toWebView:(WebView*)toWebView;
- (void)addAPIMethod:(NSString *)jsMethod withClass:(NSString *)className andSelector:(NSString *)selector;
- (NSDictionary*)getAPIMethodInfo;

@end
