#import <UIKit/UIKit.h>

#import "ForgeViewController.h"

@interface WKWebViewController : ForgeViewController <WKNavigationDelegate, WKScriptMessageHandler, WKHTTPCookieStoreObserver, WKUIDelegate> {
}

- (void)loadURL:(NSURL*)url;
- (void) forceUpdateWebView;

@end

