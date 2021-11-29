#import <Foundation/Foundation.h>
#import "ForgeTask.h"

@interface internal_API : NSObject

+ (void)ping:(ForgeTask*)task;
+ (void)showDebugWarning:(ForgeTask*)task;
+ (void)hideDebugWarning:(ForgeTask*)task;

@end
