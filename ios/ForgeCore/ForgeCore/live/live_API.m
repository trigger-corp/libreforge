#import "live_API.h"
#import "ForgeApp.h"
#import "ForgeLog.h"
#import "WKWebViewController.h"

#import "httpd_EventListener.h"

#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wundeclared-selector"

@implementation live_API

// TODO no longer works with built-in httpd
+ (void)restartApp:(ForgeTask *)task {
    dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
        [ForgeApp.sharedApp nativeEvent:@selector(applicationIsReloading) withArgs:@[]];
        [ForgeApp.sharedApp.viewController loadInitialPage];
    });
}

+ (void)restartServer:(ForgeTask *)task {
    dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
        [ForgeApp.sharedApp nativeEvent:@selector(applicationIsReloading) withArgs:@[]];
        [httpd_EventListener restartServer];
    });
}

+ (void)reloadInitialPage:(ForgeTask *)task {
    NSURL *url = [httpd_EventListener getURL];
    [ForgeLog d:[NSString stringWithFormat:@"Reloading initial page: %@", url]];
    dispatch_async(dispatch_get_main_queue(), ^{
        [ForgeApp.sharedApp.viewController loadURL:url];
    });
}

@end

#pragma clang diagnostic pop
