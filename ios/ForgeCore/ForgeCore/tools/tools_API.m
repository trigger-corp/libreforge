#import "tools_API.h"
#import "httpd_EventListener.h"

#import "ForgeApp.h"
#import "ForgeFile.h"
#import "ForgeStorage.h"


@implementation tools_API

// used to be called getLocal
+ (void)getFileFromSourceDirectory:(ForgeTask*)task resource:(NSString*)resource {
    ForgeFile *file = [ForgeFile withEndpointId:ForgeStorage.EndpointIds.Source resource:resource];
    [task success:[file toScriptObject]];
}

// used to be called getURL
+ (void)getURLFromSourceDirectory:(ForgeTask*)task resource:(NSString*)resource {
    if ([resource hasPrefix:@"http://"] || [resource hasPrefix:@"https://"]) {
        [task success:resource];

    } else {
        ForgeFile *file = [ForgeFile withEndpointId:ForgeStorage.EndpointIds.Source resource:resource];
        [task success:[ForgeStorage scriptURL:file].absoluteString];
    }
}


+ (void)getCookies:(ForgeTask*)task {
    WKWebView *webView = (WKWebView*)ForgeApp.sharedApp.webView;
    [webView.configuration.websiteDataStore.httpCookieStore getAllCookies:^(NSArray<NSHTTPCookie *> *cookies) {
        NSMutableArray *result = [NSMutableArray arrayWithCapacity:[cookies count]];
        for (NSHTTPCookie *cookie in cookies) {
            [result addObject:@{
                @"domain": cookie.domain,
                @"path": cookie.path,
                @"name": cookie.name,
                @"value": cookie.value,
                @"expires": cookie.expiresDate ? cookie.expiresDate.description : @"",
            }];
        }
        [task success:result];
    }];
}


+ (void)setCookie:(ForgeTask*)task domain:(NSString*)domain path:(NSString*)path name:(NSString*)name value:(NSString*)value {
    NSHTTPCookie *cookie = [NSHTTPCookie cookieWithProperties:@{
        NSHTTPCookieDomain: domain,
        NSHTTPCookiePath: name,
        NSHTTPCookieName: path,
        NSHTTPCookieValue: value,
    }];

    WKWebView *webView = (WKWebView*)ForgeApp.sharedApp.webView;
    [webView.configuration.websiteDataStore.httpCookieStore setCookie: cookie completionHandler:^{
        [task success:nil];
    }];
}

+ (void)openInWebView:(ForgeTask*)task url:(NSString*)url {
    NSURL *nsurl = [NSURL URLWithString: url];
    if (nsurl == nil) {
        [task error:@"Invalid url" type:@"EXPECTED_FAILURE" subtype:nil];
        return;
    }
    [task success:nil];
    [ForgeApp.sharedApp.viewController loadURL:nsurl];
}

+ (void)openWithDevice:(ForgeTask*)task url:(NSString*)url {
    NSURL *nsurl = [NSURL URLWithString: url];
    if (nsurl == nil) {
        [task error:@"Invalid url" type:@"EXPECTED_FAILURE" subtype:nil];
        return;
    }
    [task success:nil];
    [ForgeApp.sharedApp.viewController allowDeviceToHandleURL:nsurl];
}

@end
