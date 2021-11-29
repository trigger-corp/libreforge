#import "event_EventListener.h"
#import "Reachability.h"
#import "ForgeLog.h"
#import "ForgeApp.h"
#import "ForgeCore.h"

static BOOL _connectionConnected = NO;
static BOOL _connectionWifi = NO;

@implementation event_EventListener
+ (void)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
	TMReachability* reach = [TMReachability reachabilityForInternetConnection];

	reach.reachableBlock = ^(TMReachability *reach) {
		_connectionConnected = [reach isReachable];
		_connectionWifi = [reach isReachableViaWiFi];
		[self sendEvent];
		[ForgeLog d:@"Internet connection available"];
	};
	reach.unreachableBlock = ^(TMReachability *reach) {
		_connectionConnected = [reach isReachable];
		_connectionWifi = [reach isReachableViaWiFi];
		[self sendEvent];
		[ForgeLog d:@"Internet connection lost"];
	};

	[reach startNotifier];
	_connectionConnected = [reach isReachable];
	_connectionWifi = [reach isReachableViaWiFi];
}

+ (void) firstWebViewLoad {
	// Send first event
	[self sendEvent];
}

+ (void) applicationDidEnterBackground:(UIApplication *)application {
	[ForgeApp.sharedApp event:@"event.appPaused" withParam:[NSNull null]];
}

+ (void) applicationWillEnterForeground:(UIApplication *)application {
    // TODO a truly ugly hack :-/
    if ([ForgeApp.sharedApp flag:@"ios_disable_httpd"] != YES) {
        NSLog(@"event_EventListener applicationWillEnterForeground delaying event.appResumed until httpd has finished starting");
        return;
    }
	[ForgeApp.sharedApp event:@"event.appResumed" withParam:[NSNull null]];
}

+ (void)touchesBegan:(NSSet *)touches withEvent:(UIEvent *)event {
	if (floor(NSFoundationVersionNumber) >= NSFoundationVersionNumber_iOS_9_0) {
		CGPoint location = [[[event allTouches] anyObject] locationInView:[ForgeApp.sharedApp.appDelegate window]];
		CGRect statusBarFrame = [UIApplication sharedApplication].statusBarFrame;
		if (CGRectContainsPoint(statusBarFrame, location)) {
			[ForgeApp.sharedApp event:@"event.statusBarTapped" withParam:[NSNull null]];
		}
	}

}

+ (void)touchesEnded:(NSSet *)touches withEvent:(UIEvent *)event {
	if (floor(NSFoundationVersionNumber) < NSFoundationVersionNumber_iOS_9_0) {
		CGPoint location = [[[event allTouches] anyObject] locationInView:[ForgeApp.sharedApp.appDelegate window]];
		CGRect statusBarFrame = [UIApplication sharedApplication].statusBarFrame;
		if (CGRectContainsPoint(statusBarFrame, location)) {
			[ForgeApp.sharedApp event:@"event.statusBarTapped" withParam:[NSNull null]];
		}
	}
}

+ (void)viewWillTransitionToSize:(CGSize)size withTransitionCoordinator:(id<UIViewControllerTransitionCoordinator>)coordinator {
    [coordinator animateAlongsideTransition:nil completion:^(id<UIViewControllerTransitionCoordinatorContext>  _Nonnull context) {
        if (UIDeviceOrientationIsLandscape(UIDevice.currentDevice.orientation)) {
            [ForgeApp.sharedApp event:@"internal.orientationChange" withParam:@{ @"orientation": @"landscape" }];
        } else if (UIDeviceOrientationIsPortrait(UIDevice.currentDevice.orientation)) {
            [ForgeApp.sharedApp event:@"internal.orientationChange" withParam:@{ @"orientation": @"portrait" }];
        }
    }];
}


// Keyboard Management:
// https://developer.apple.com/library/archive/documentation/StringsTextFonts/Conceptual/TextAndWebiPhoneOS/KeyboardManagement/KeyboardManagement.html

+ (void)keyboardWillShow:(NSNotification*)notification {
    NSDictionary* info = [notification userInfo];
    CGSize keyboardSize = [[info objectForKey:UIKeyboardFrameEndUserInfoKey] CGRectValue].size;
    [ForgeApp.sharedApp event:@"event.keyboardWillShow" withParam:@{
        @"height" : [NSNumber numberWithFloat:(keyboardSize.height)],
        @"width"  : [NSNumber numberWithFloat:(keyboardSize.width)]
    }];
}

+ (void)keyboardWillHide:(NSNotification*)notification {
    [ForgeApp.sharedApp event:@"event.keyboardWillHide" withParam:@{
        @"height" : [NSNumber numberWithFloat:(0)],
        @"width"  : [NSNumber numberWithFloat:(0)]
    }];
}

+ (void)keyboardDidShow:(NSNotification*)notification {
    NSDictionary* info = [notification userInfo];
    CGSize keyboardSize = [[info objectForKey:UIKeyboardFrameEndUserInfoKey] CGRectValue].size;
    [ForgeApp.sharedApp event:@"event.keyboardDidShow" withParam:@{
        @"height" : [NSNumber numberWithFloat:(keyboardSize.height)],
        @"width"  : [NSNumber numberWithFloat:(keyboardSize.width)]
    }];
}

+ (void)keyboardDidHide:(NSNotification*)notification {
    [ForgeApp.sharedApp event:@"event.keyboardDidHide" withParam:@{
        @"height" : [NSNumber numberWithFloat:(0)],
        @"width"  : [NSNumber numberWithFloat:(0)]
    }];
}

+ (BOOL) connectionConnected { return _connectionConnected; }
+ (BOOL) connectionWifi      { return _connectionWifi; }

// Private

+ (void) sendEvent {
	[ForgeApp.sharedApp event:@"internal.connectionStateChange" withParam:[NSDictionary dictionaryWithObjectsAndKeys:[NSNumber numberWithBool:_connectionConnected], @"connected", [NSNumber numberWithBool:_connectionWifi], @"wifi", nil]];
}

@end
