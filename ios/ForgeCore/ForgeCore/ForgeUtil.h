#import <Foundation/Foundation.h>

@interface ForgeUtil : NSObject

@property (class, nonatomic, assign, readonly) BOOL isIphone;
@property (class, nonatomic, assign, readonly) BOOL isIphone_xr;
@property (class, nonatomic, assign, readonly) BOOL isIpad;
@property (class, nonatomic, assign, readonly) BOOL isDeviceWithNotch;

+ (BOOL)isIphone;
+ (BOOL)isIphone_xr;
+ (BOOL)isDeviceWithNotch;

+ (BOOL) url:(NSString*)url matchesPattern:(NSString*)pattern;

+ (NSData*)sendSynchronousRequest:(NSURLRequest*)request returningResponse:(NSURLResponse**)response error:(NSError**)error;

@end


