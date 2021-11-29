#import "ForgeApp.h"
#import "ForgeTask.h"
#import "ForgeLog.h"

static ForgeApp *sharedSingleton;

@implementation ForgeApp

@synthesize webView, appConfig, appDelegate, eventListeners, inspectorEnabled, storedAPIMethods;

+ (void)initialize {
	static BOOL initialized = NO;
	if (!initialized) {
		initialized = YES;
		sharedSingleton = [[ForgeApp alloc] init];
		sharedSingleton.appConfig = [[[NSString alloc] initWithData:[[NSFileManager defaultManager] contentsAtPath:[[NSBundle mainBundle] pathForResource:@"assets/app_config.json" ofType:@""]] encoding:NSUTF8StringEncoding] objectFromJSONString];
		sharedSingleton.eventListeners = [[NSMutableArray alloc] init];
		sharedSingleton.inspectorEnabled = NO;
		sharedSingleton.storedAPIMethods = [[NSMutableDictionary alloc] init];
	}
}

/**
 * Access shared singleton
 */
+ (ForgeApp*)sharedApp {
	return sharedSingleton;
}

- (void)event:(NSString *)name withParam:(id)params {
	if (params == nil) {
		params = [NSNull null];
	}
	NSDictionary *returnObj = @{@"params" : params, @"event" : name};

	// Send the event back to the webview from the main thread
	if ([NSThread isMainThread]) {
		[self returnResult:returnObj toWebView:webView];
	} else {
		dispatch_async(dispatch_get_main_queue(), ^{
			[self returnResult:returnObj toWebView:webView];
		});
	}
}

- (void)addAPIMethod:(NSString *)jsMethod withClass:(NSString *)className andSelector:(NSString *)selector {
	[storedAPIMethods setObject:[NSArray arrayWithObjects:className, selector, nil] forKey:jsMethod];
}

- (void) callNativeFromJavaScript:(NSString *)callid :(NSString *)method :(NSString *)params {
	[ForgeLog d:[NSString stringWithFormat:@"Native call: %@", @{@"callid": callid, @"method": method, @"params": params}]];

	// Perform a task
	NSDictionary *paramsDict = [params objectFromJSONString];
	ForgeTask *task = [[ForgeTask alloc] initWithID:callid andParams:paramsDict andWebView:webView];

	// Look up the method for this API call
	NSArray *thisCall = [storedAPIMethods objectForKey:method];

	// Check we found a matching API method
	if ([thisCall count] != 2) {
		[task error:@"Invalid API method" type:@"UNAVAILABLE" subtype:nil];
		[ForgeLog w:@"Invalid API method"];
		return;
	}

	// Check the API class exists
	Class APIClass = NSClassFromString([thisCall objectAtIndex:0]);
	if (APIClass == nil) {
		[task error:@"Invalid API method" type:@"UNAVAILABLE" subtype:nil];
		[ForgeLog w:@"Invalid API method"];
		return;
	}

	// Check the API method exists
	SEL APIMethod = NSSelectorFromString([thisCall objectAtIndex:1]);
	if ([APIClass respondsToSelector:APIMethod] == NO) {
		[task error:@"Invalid API method" type:@"UNAVAILABLE" subtype:nil];
		[ForgeLog w:@"Invalid API method"];
		return;
	}

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
			id param = [paramsDict objectForKey:paramKey];
			[inv setArgument:&param atIndex:i+2];
		}

		[inv invoke];
	}
	@catch (NSException *exception) {
		[task error:[exception description]];
	}
}

- (void)returnResult:(NSDictionary *)data toWebView:(WebView*)toWebView {

	// Return the result of an async task to Javascript
	// Only call this method from the main thread
	[ForgeLog d:[NSString stringWithFormat:@"Returning to javascript: %@", data]];
    NSString *jsonData = [data JSONString];
    if ( jsonData == nil ) {
        jsonData = @"null";
    }
	[toWebView stringByEvaluatingJavaScriptFromString:[@"window.forge._receive(" stringByAppendingString:[jsonData stringByAppendingString:@")"]]];
}


- (NSDictionary*)getAPIMethodInfo {
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

@end
