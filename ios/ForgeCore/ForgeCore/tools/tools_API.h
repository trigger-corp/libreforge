#import <Foundation/Foundation.h>
#import "ForgeTask.h"

@interface tools_API : NSObject

+ (void)getURLFromSourceDirectory:(ForgeTask*)task resource:(NSString*)resource;
+ (void)getFileFromSourceDirectory:(ForgeTask*)task resource:(NSString*)resource;

+ (void)getCookies:(ForgeTask*)task;
+ (void)setCookie:(ForgeTask*)task domain:(NSString*)domain path:(NSString*)path name:(NSString*)name value:(NSString*)value;

@end
