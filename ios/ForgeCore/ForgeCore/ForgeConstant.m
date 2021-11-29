#import "ForgeApp.h"
#import "ForgeConstant.h"
#import "ForgeViewController.h"
#import "ForgeUtil.h"

@implementation ForgeConstant

// NOTE Careful with dynamic methods, the result depends on whether the element is visible or not!
// TODO implement dynamic and static versions for all elements


+ (CGFloat)statusBarHeightDynamic {
    CGFloat statusBarHeight = UIApplication.sharedApplication.statusBarFrame.size.height;
    // NSLog(@"statusBarHeight is 0.0, 20.0 or 44.0 => %f pixels high", statusBarHeight);

    return statusBarHeight; // 20.0f, 44.0f on iPhone-X
}


+ (CGFloat)navigationBarHeightStatic {
    //UINavigationController *navigationBarController = [UINavigationController new];
    //CGFloat navigationBarHeight = navigationBarController.navigationBar.frame.size.height;
    // NSLog(@"UINavigationBar is 44.0 => %f pixels high", navigationBarHeight);
    return 44.0f;
}


+ (CGFloat)navigationBarHeightDynamic {
    CGFloat navigationBarHeight = ForgeApp.sharedApp.viewController.navigationBar.bounds.size.height;
    // NSLog(@"UINavigationBar is 44.0 => %f pixels high", navigationBarHeight);
    return navigationBarHeight;
}


+ (CGFloat)tabBarHeightDynamic {
    UITabBarController *tabBarController = [UITabBarController new];
    CGFloat tabBarHeight = tabBarController.tabBar.frame.size.height;
    // NSLog(@"UITabBar is 49.0 => %f pixels high", tabBarHeight);
    return tabBarHeight; // 49.0f, 83.0f on iPhone-X
}


+ (CGFloat)screenWidth {
    return [[UIScreen mainScreen] bounds].size.width;
}


+ (CGFloat)screenHeight {
    return [[UIScreen mainScreen] bounds].size.height;
}


@end
