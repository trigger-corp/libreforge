#import <Foundation/Foundation.h>
#import <WebKit/WebKit.h>

@interface ForgeTask : NSObject
{
	UIBackgroundTaskIdentifier bgTask;
	WKWebView* webView;
}

@property (readonly) NSString *callid;
@property (readonly) NSDictionary *params;

- (ForgeTask*) initWithID:(NSString*)newcallid andParams:(NSDictionary*)newparams andWebView:(WKWebView *)newWebView;
- (void) success:(id)result;
- (void) error:(id)e;
- (void) error:(NSString*)message type:(NSString*)type subtype:(NSString*)subtype;
- (void) errorDict:(NSDictionary*)result;
- (void) errorString:(NSString*)message;
- (void) errorThrown:(NSException*)e;
- (void) runInBackground;


@end
