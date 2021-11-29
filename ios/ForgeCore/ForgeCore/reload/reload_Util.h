#import <UIKit/UIKit.h>
#import "ForgeTask.h"

@interface reload_Util : NSObject

+ (BOOL)updateAvailable;
+ (void)updateWithLock:(ForgeTask*)task;
+ (void)applyUpdate:(ForgeTask*)task;
+ (NSString*)getUpdateState;
+ (void)setUpdateState:(NSString*)updateState;
+ (BOOL)reloadManual;
+ (BOOL)reloadEnabled;
+ (NSString*) stringWithContentsOfURL:(NSURL*)url;
@end
