#import <Foundation/Foundation.h>
#import <WebKit/WebKit.h>

@interface BorderControl : NSObject {
}

+ (void)runTask:(NSDictionary *)data forWebView:(WKWebView*)webView;
+ (void)returnResult:(NSDictionary *)data toWebView:(WKWebView*)webView;
+ (void)addAPIMethod:(NSString *)jsMethod withClass:(NSString *)className andSelector:(NSString *)selector;
+ (NSDictionary*)getAPIMethodInfo;

@end
