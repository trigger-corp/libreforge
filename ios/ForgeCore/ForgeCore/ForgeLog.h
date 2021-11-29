#import <Foundation/Foundation.h>

@interface ForgeLog : NSObject {
}

@property (class, nonatomic, readonly) BOOL isSimulator;

+ (void)start;
+ (void)setLogLevel:(NSString*)level;
+ (void) d:(id)msg;
+ (void) i:(id)msg;
+ (void) w:(id)msg;
+ (void) e:(id)msg;
+ (void) c:(id)msg;

@end
