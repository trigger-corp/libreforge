#import <Foundation/Foundation.h>
#import "ForgeTask.h"

@interface layout_API : NSObject

+ (void)setStatusBarHidden:(ForgeTask*)task hidden:(NSNumber*)hidden;
+ (void)setStatusBarTransparent:(ForgeTask*)task transparent:(NSNumber*)transparent;
+ (void)setStatusBarColor:(ForgeTask *)task color:(NSArray*)color;
+ (void)setStatusBarStyle:(ForgeTask*)task style:(NSString*)style;

+ (void)setNavigationBarHidden:(ForgeTask*)task hidden:(NSNumber*)hidden;
+ (void)setTabBarHidden:(ForgeTask*)task hidden:(NSNumber*)hidden;

+ (void)getSafeAreaInsets:(ForgeTask*)task;

@end
