#import "ForgeTask.h"
#import "BorderControl.h"
#import "ForgeLog.h"
#import "ForgeApp.h"
#import "event_EventListener.h"


/**
 * A ForgeTask contains details about a native API call from Javascript, and has several helper methods to perform common tasks from a native API call.
 */
@implementation ForgeTask

@synthesize params, callid;

- (ForgeTask*) initWithID:(NSString *)newcallid andParams:(NSDictionary *)newparams andWebView:(WKWebView *)newWebView {
	self = [super init];
	if (self != nil) {
		callid = newcallid;
		params = newparams;
		bgTask = UIBackgroundTaskInvalid;
		webView = newWebView;
	}
	return self;
}

/**
 * Return success with a result to Javascript for the task
 * @param result A JSON serializable object to return
 */
- (void) success:(id)result {
	NSDictionary *returnObj = @{
		@"content": result ? result : [NSNull null],
		@"status": @"success",
		@"callid": callid
	};

	// Pass the result of the async task back to the webview from the main thread
	if ([NSThread isMainThread]) {
		[BorderControl returnResult:returnObj toWebView:webView];
	} else {
		dispatch_async(dispatch_get_main_queue(), ^{
            [BorderControl returnResult:returnObj toWebView:self->webView];
		});
	}

	if (bgTask != UIBackgroundTaskInvalid) {
		UIApplication *app = [UIApplication sharedApplication];
		[app endBackgroundTask:bgTask];
		bgTask = UIBackgroundTaskInvalid;
	}
}

// No method overloading, manually switch between types of error
- (void) error:(id)e {
	if ([e isKindOfClass:[NSString class]]) {
		[self errorString:e];
	} else if ([e isKindOfClass:[NSDictionary class]]) {
		[self errorDict:e];
	} else if ([e isKindOfClass:[NSException class]]) {
		[self errorThrown:e];
	} else {
		[self errorString:@"Unknown error"];
		[ForgeLog w:@"Unknown error in API method"];
	}
}

/**
 * Return an error to Javascript.
 * @param message Human readable error message
 * @param type One of UNEXPECTED_FAILURE, EXPECTED_FAILURE, UNAVAILABLE or BAD_INPUT
 * @param subtype An easily matchable error code for errors that need to be programmatically filtered
 */
- (void) error:(NSString *)message type:(NSString *)type subtype:(NSString *)subtype {
	[self errorDict:@{
		@"message": message ? message : [NSNull null],
		@"type": type ? type : [NSNull null],
		@"subtype": subtype ? subtype : [NSNull null],
	 }];
}

- (void) errorDict:(NSDictionary *)result {
	// Something went wrong, format an error return object
	NSDictionary *returnObj = @{
		@"content": result ? result : [NSNull null],
		@"status": @"error",
		@"callid": callid
	};

	if ([NSThread isMainThread]) {
		[BorderControl returnResult:returnObj toWebView:webView];
	} else {
		dispatch_async(dispatch_get_main_queue(), ^{
            [BorderControl returnResult:returnObj toWebView:self->webView];
		});
	}

	if (bgTask != UIBackgroundTaskInvalid) {
		UIApplication *app = [UIApplication sharedApplication];
		[app endBackgroundTask:bgTask];
		bgTask = UIBackgroundTaskInvalid;
	}
}

- (void) errorString:(NSString *)message {
	[self errorDict:[NSDictionary dictionaryWithObjectsAndKeys:
					 message,
					 @"message",
					 @"UNEXPECTED_FAILURE",
					 @"type",
					 nil]];
}

- (void) errorThrown:(NSException*)e {
	[self errorDict:[NSDictionary dictionaryWithObjectsAndKeys:
					 [@"Forge exception: " stringByAppendingString:[e reason]],
					 @"message",
					 @"UNEXPECTED_FAILURE",
					 @"type",
					 nil]];
}

/**
 * Inform the device that this task should be allowed to continue in the background.
 *
 * The task many still be paused if it takes longer than 10 minutes or for other reasons.
 */
- (void) runInBackground {
	UIApplication *app = [UIApplication sharedApplication];
	if ([app respondsToSelector:@selector(beginBackgroundTaskWithExpirationHandler:)] && bgTask == UIBackgroundTaskInvalid) {
		bgTask = [app beginBackgroundTaskWithExpirationHandler:^{
            if (self->bgTask != UIBackgroundTaskInvalid) {
                [app endBackgroundTask:self->bgTask];
                self->bgTask = UIBackgroundTaskInvalid;
			}
		}];
	}
}

- (BOOL) internetReachable {
	return [event_EventListener connectionConnected];
}

- (ForgeViewController*) viewController {
	return ForgeApp.sharedApp.viewController;
}

- (WKWebView*) webView {
	return ForgeApp.sharedApp.webView;
}

@end
