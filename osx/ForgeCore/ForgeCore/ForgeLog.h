#import <Foundation/Foundation.h>

@interface ForgeLog : NSObject {

}

+ (void) d:(id)msg;
+ (void) i:(id)msg;
+ (void) w:(id)msg;
+ (void) e:(id)msg;
+ (void) c:(id)msg;

@end
