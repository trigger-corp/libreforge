#import <Foundation/Foundation.h>

@interface ForgeTask : NSObject
{
	WebView* webView;
}

@property (readonly) NSString *callid;
@property (readonly) NSDictionary *params;

- (ForgeTask*) initWithID:(NSString*)newcallid andParams:(NSDictionary*)newparams andWebView:(WebView *)newWebView;
- (void) success:(id)result;
- (void) error:(id)e;
- (void) error:(NSString*)message type:(NSString*)type subtype:(NSString*)subtype;
- (void) errorDict:(NSDictionary*)result;
- (void) errorString:(NSString*)message;
- (void) errorThrown:(NSException*)e;


@end
