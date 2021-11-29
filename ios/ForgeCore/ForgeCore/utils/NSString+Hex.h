#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

@interface NSString (Hex)

+ (NSString*) stringFromHex:(NSString*)str;
+ (NSString*) stringToHex:(NSString*)str;

@end

NS_ASSUME_NONNULL_END


