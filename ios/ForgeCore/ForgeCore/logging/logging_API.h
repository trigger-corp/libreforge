#import <Foundation/Foundation.h>
#import "ForgeTask.h"

@interface logging_API : NSObject

+ (void)log:(ForgeTask*)task message:(NSString *)message level:(NSNumber *)level;

@end
