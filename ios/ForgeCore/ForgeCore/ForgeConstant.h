#import <Foundation/Foundation.h>

/**
 * Things are added here in the hopes that, one day, we no longer need them.
 */
@interface ForgeConstant : NSObject

@property (class, nonatomic, assign, readonly) CGFloat statusBarHeightDynamic;
@property (class, nonatomic, assign, readonly) CGFloat navigationBarHeightStatic;
@property (class, nonatomic, assign, readonly) CGFloat navigationBarHeightDynamic;
@property (class, nonatomic, assign, readonly) CGFloat tabBarHeightDynamic;
@property (class, nonatomic, assign, readonly) CGFloat screenHeight;
@property (class, nonatomic, assign, readonly) CGFloat screenWidth;

// auto layout is only 1/3 of a solution until it can also manage insets
+ (CGFloat)statusBarHeightDynamic;
+ (CGFloat)navigationBarHeightStatic;
+ (CGFloat)navigationBarHeightDynamic;
+ (CGFloat)tabBarHeightDynamic;
+ (CGFloat)screenWidth;
+ (CGFloat)screenHeight;

@end

