#import "ForgeJSBridge.h"
#import "ForgeApp.h"

@implementation ForgeJSBridge

- (void) callNativeFromJavaScript:(NSString *)callid :(NSString *)method :(NSString *)params {
	dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
		[[ForgeApp sharedApp] callNativeFromJavaScript:callid :method :params];
	});
}
+ (BOOL)isSelectorExcludedFromWebScript:(SEL)sel {
	if (sel == @selector(callNativeFromJavaScript:::)) {
		return NO;
	}
	return YES;
}
+ (NSString *) webScriptNameForSelector:(SEL)sel {
	if (sel == @selector(callNativeFromJavaScript:::)) {
		return @"callNativeFromJavaScript";
	}
	return nil;
}

@end
