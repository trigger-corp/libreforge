#import "ForgeApp.h"
#import "ForgeViewController.h"
#import "ForgeLog.h"
#import "ForgeConstant.h"

#import "layout_API.h"

@implementation layout_API

+ (void)setStatusBarHidden:(ForgeTask*)task hidden:(NSNumber*)hidden
{
    ForgeApp.sharedApp.viewController.statusBarHidden = [hidden boolValue];
    [task success:nil];
}


+ (void)setStatusBarTransparent:(ForgeTask*)task transparent:(NSNumber*)transparent
{
    ForgeApp.sharedApp.viewController.statusBarTransparent = [transparent boolValue];
    [task success:nil];
}


+ (void)setStatusBarColor:(ForgeTask *)task color:(NSArray*)color {
    [ForgeLog d:@"setStatusBarColor is only supported on Android"];
    [task success:nil];
}


+ (void)setStatusBarStyle:(ForgeTask*)task style:(NSString*)style {
    if ([style isEqualToString:@"light_content"] || [style isEqualToString:@"UIStatusBarStyleLightContent"]) {
        ForgeApp.sharedApp.viewController.statusBarStyle = UIStatusBarStyleLightContent;
    } else if ([style isEqualToString:@"dark_content"] || [style isEqualToString:@"UIStatusBarStyleDarkContent"]) {
        if (@available(iOS 13.0, *)) {
            ForgeApp.sharedApp.viewController.statusBarStyle = UIStatusBarStyleDarkContent;
        } else {
            ForgeApp.sharedApp.viewController.statusBarStyle = UIStatusBarStyleDefault;
        }
    } else if ([style isEqualToString:@"default"] || [style isEqualToString:@"UIStatusBarStyleDefault"]) {
        ForgeApp.sharedApp.viewController.statusBarStyle = UIStatusBarStyleDefault;
    }
    [task success:nil];
}


+ (void)setNavigationBarHidden:(ForgeTask*)task hidden:(NSNumber*)hidden
{
    ForgeApp.sharedApp.viewController.navigationBarHidden = [hidden boolValue];
    [task success:nil];
}


+ (void)setTabBarHidden:(ForgeTask*)task hidden:(NSNumber*)hidden
{
    ForgeApp.sharedApp.viewController.tabBarHidden = [hidden boolValue];
    [task success:nil];
}


+ (void)getSafeAreaInsets:(ForgeTask*)task
{
    UIEdgeInsets insets = ForgeApp.sharedApp.webView.safeAreaInsets;

    if (ForgeApp.sharedApp.viewController.navigationBarHidden == NO) {
        insets.top += ForgeConstant.navigationBarHeightDynamic;
    }

    if (ForgeApp.sharedApp.viewController.tabBarHidden == NO) {
        insets.bottom += ForgeConstant.tabBarHeightDynamic;
    }

    [task success:@{
        @"left"   : [NSNumber numberWithFloat:insets.left],
        @"top"    : [NSNumber numberWithFloat:insets.top],
        @"right"  : [NSNumber numberWithFloat:insets.right],
        @"bottom" : [NSNumber numberWithFloat:insets.bottom]
    }];
}

@end
