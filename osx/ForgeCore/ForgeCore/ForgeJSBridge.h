#import <Foundation/Foundation.h>

@interface ForgeJSBridge : NSObject

- (void) callNativeFromJavaScript:(NSString *)callid:(NSString *)method:(NSString *)params;
+ (BOOL)isSelectorExcludedFromWebScript:(SEL)sel;
+ (NSString *) webScriptNameForSelector:(SEL)sel;

@end
