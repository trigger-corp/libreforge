#import <Foundation/Foundation.h>
#import "ForgeTask.h"

@interface reload_API : NSObject

+ (void)updateAvailable:(ForgeTask*)task;
+ (void)update:(ForgeTask*)task;
+ (void)applyAndRestartApp:(ForgeTask*)task;
+ (void)switchStream:(ForgeTask*)task streamid:(NSString*)streamId;

@end
