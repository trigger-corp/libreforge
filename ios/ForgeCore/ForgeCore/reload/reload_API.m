#import "NSString+ObjectFromJSONString.h"

#import "reload_API.h"
#import "reload_Util.h"
#import "ForgeApp.h"
#import "ForgeLog.h"
#import "WKWebViewController.h"

#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wundeclared-selector"

@implementation reload_API

+ (void)updateAvailable:(ForgeTask*)task {
	dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_LOW, 0), ^{
		if ([reload_Util reloadEnabled] && [reload_Util updateAvailable]) {
			[task success:[NSNumber numberWithBool:YES]];
		} else {
			[task success:[NSNumber numberWithBool:NO]];
		}
	});
}

+ (void)update:(ForgeTask*)task {
	if ([reload_Util reloadEnabled] && [[reload_Util getUpdateState] isEqualToString:@"paused"]) {
		[ForgeLog i:@"Resuming Reload updates"];
		reload_Util.updateState = @"";
	}
	dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_LOW, 0), ^{
		[reload_Util updateWithLock:task];
	});
}

+ (void)applyAndRestartApp:(ForgeTask *)task {
	dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
		[ForgeApp.sharedApp nativeEvent:@selector(applicationIsReloading) withArgs:@[]];
		[reload_Util applyUpdate:task];
		[ForgeApp.sharedApp.viewController loadInitialPage];
	});
}

+ (void)switchStream:(ForgeTask*)task streamid:(NSString*)streamId {
	NSRegularExpression *regex = [NSRegularExpression regularExpressionWithPattern:@"^[a-z0-9_-]+$" options:0 error:nil];
	if ([regex numberOfMatchesInString:streamId options:0 range:NSMakeRange(0, [streamId length])] == 0) {
		[task error:@"Invalid stream name" type:@"EXPECTED_FAILURE" subtype:nil];
		return;
	}
    if ([reload_Util reloadEnabled]) {
        NSDictionary *appConfig = ForgeApp.sharedApp.appConfig;
        NSString *updateUrl = [NSString stringWithFormat:@"%@/api/reload/%@/streams/%@", [appConfig objectForKey:@"trigger_domain"], [appConfig objectForKey:@"uuid"], streamId];
        NSString *updateResult = [reload_Util stringWithContentsOfURL:[NSURL URLWithString:updateUrl]];
        NSDictionary *updateDict = [updateResult objectFromJSONString];
        if ([[updateDict objectForKey:@"result"] isEqualToString:@"ok"]) {
            NSUserDefaults *prefs = [NSUserDefaults standardUserDefaults];
            [prefs setValue:streamId forKey:@"reload-stream"];
            [task success:nil];
        } else {
            [task error:@"Stream not found" type:@"EXPECTED_FAILURE" subtype:nil];
        }
    } else {
        [task error:@"Reload is disabled or device has no network connectivity" type:@"EXPECTED_FAILURE" subtype:nil];
    }
}

+ (void)pauseUpdate:(ForgeTask*)task {
	reload_Util.updateState = @"paused";
}

@end

#pragma clang diagnostic pop
