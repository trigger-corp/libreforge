#import "NSDictionary+JSONString.h"

#import "BorderControl.h"
#import "ForgeTask.h"
#import "ForgeLog.h"
#import "ForgeApp.h"

static NSMutableDictionary *storedAPIMethods;
static NSMutableArray *javascriptReturnQueue;

@implementation BorderControl

+ (void)initialize {
	storedAPIMethods = [[NSMutableDictionary alloc] init];
	javascriptReturnQueue = [[NSMutableArray alloc] init];
}

+ (void)addAPIMethod:(NSString *)jsMethod withClass:(NSString *)className andSelector:(NSString *)selector {
	[storedAPIMethods setObject:[NSArray arrayWithObjects:className, selector, nil] forKey:jsMethod];
}

+ (NSDictionary*)getAPIMethodInfo {
	NSMutableDictionary *result = [[NSMutableDictionary alloc] init];

	for (NSString *key in storedAPIMethods) {
		NSMutableDictionary *details = [[NSMutableDictionary alloc] init];
		NSString *method = [[storedAPIMethods objectForKey:key] objectAtIndex:1];
		NSArray *parts = [method componentsSeparatedByString:@":"];
		for (int i = 1; i < [parts count] - 1; i++) {
			NSString *paramKey = [parts objectAtIndex:i];
			[details setValue:[[NSDictionary alloc] init] forKey:paramKey];
		}
		[result setValue:details forKey:key];
	}

	return result;
}

// The Cordova equivalent can be found here: https://github.com/apache/cordova-ios/blob/master/CordovaLib/Classes/Public/CDVCommandQueue.m#L160
// Also see: http://stackoverflow.com/questions/17263354/why-shouldnt-you-use-objc-msgsend-in-objective-c
//           https://issues.apache.org/jira/browse/CB-6150


+ (void)runTask:(NSDictionary *)data forWebView:(WKWebView*)webView {
	// Perform a task
	NSDictionary *params = [data objectForKey:@"params"];
	ForgeTask *task = [[ForgeTask alloc] initWithID:[data objectForKey:@"callid"] andParams:params andWebView:webView];

	// Look up the method for this API call
	NSString *method = [data objectForKey:@"method"];
	NSArray *thisCall = [storedAPIMethods objectForKey:method];

	// Check we found a matching API method
	if ([thisCall count] != 2) {
		[task error:[NSString stringWithFormat:@"Method API not supported on this platform: %@", method] type:@"UNAVAILABLE" subtype:nil];
		[ForgeLog w:[NSString stringWithFormat:@"Method API not supported on this platform: %@", method]];
		return;
	}

	// Check the API class exists
	Class APIClass = NSClassFromString([thisCall objectAtIndex:0]);
	if (APIClass == nil) {
		[task error:[NSString stringWithFormat:@"Method class not supported on this platform: %@", method] type:@"UNAVAILABLE" subtype:nil];
		[ForgeLog w:[NSString stringWithFormat:@"Method class not supported on this platform: %@", method]];
		return;
	}

	// Check the API method exists
	SEL APIMethod = NSSelectorFromString([thisCall objectAtIndex:1]);
	// Okay, if Apple thinks it's more secure to _not_ check then we'll just have to not check then won't we?
	/*if ([APIClass respondsToSelector:APIMethod] == NO) {
		[task error:[NSString stringWithFormat:@"Method not supported on this platform: %@", method] type:@"UNAVAILABLE" subtype:nil];
		[ForgeLog w:[NSString stringWithFormat:@"Method not supported on this platform: %@", method]];
		return;
	}*/

	// Run the method
	@try {
		NSMethodSignature *sig = [APIClass methodSignatureForSelector:APIMethod];
		NSInvocation *inv = [NSInvocation invocationWithMethodSignature:sig];
		[inv setTarget:APIClass];
		[inv setSelector:APIMethod];
		[inv setArgument:&task atIndex:2];

		NSString *method = [thisCall objectAtIndex:1];
		NSArray *parts = [method componentsSeparatedByString:@":"];
		for (int i = 1; i < [parts count] - 1; i++) {
			NSString *paramKey = [parts objectAtIndex:i];
			id param = [params objectForKey:paramKey];
			[inv setArgument:&param atIndex:i+2];
		}

		[inv invoke];
	}
	@catch (NSException *exception) {
		[task error:[exception description]];
	}
}

+ (void)returnResult:(NSDictionary *)data toWebView:(WKWebView*)webView {
	// Return the result of an async task to Javascript
	// Only call this method from the main thread
	if (data == nil || webView == nil) {
		return;
	}
	[javascriptReturnQueue addObject:@[data, webView]];
	NSMutableArray *currentQueue = javascriptReturnQueue;
	javascriptReturnQueue = [[NSMutableArray alloc] init];

	__block BOOL hasFailed = NO;
	[currentQueue enumerateObjectsUsingBlock:^(id obj, NSUInteger idx, BOOL *stop) {
		NSDictionary *data = [obj objectAtIndex:0];
		if (hasFailed) {
			[javascriptReturnQueue addObject:obj];
		} else {
			NSString *jsonData = [data JSONString];
			if ( jsonData == nil ) {
				jsonData = @"null";
			}

            [(WKWebView*)[obj objectAtIndex:1]  evaluateJavaScript:[@"window.forge._receive(" stringByAppendingString:[jsonData stringByAppendingString:@")"]] completionHandler:^(id result, NSError *error) {
                if (![result isEqualToString:@"success"]) {
                    hasFailed = YES;
                    [javascriptReturnQueue addObject:obj];
                } else {
                    bool isLoggingNoise = false;
                    if (data[@"content"] && [data[@"content"] isKindOfClass:[NSDictionary class]] && data[@"content"][@"method"]) {
                        NSString *method = data[@"content"][@"method"];
                        isLoggingNoise = [method isEqualToString:@"logging.log"];
                    }
                    if (!isLoggingNoise) {
                        [ForgeLog d:[NSString stringWithFormat:@"Returned to javascript: %@", data]];
                    }
                }
            }];
		}
	}];
}

@end
