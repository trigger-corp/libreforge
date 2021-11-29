#import <ForgeCore/ForgeApp.h>

#import "internal_API.h"

static UIAlertController *debugWarning;

@implementation internal_API

+ (void)ping:(ForgeTask*)task {
	[task success:[task.params objectForKey:@"data"]];
}

+ (void)showDebugWarning:(ForgeTask*)task {
    NSString *title = @"Waiting for Catalyst...";
    NSString *message = @"Waiting for connection to Catalyst\n\nThis is because your code includes 'forge.enableDebug();'";
    debugWarning = [UIAlertController alertControllerWithTitle:title
                                                       message:message
                                                preferredStyle:UIAlertControllerStyleAlert];
    dispatch_async(dispatch_get_main_queue(), ^{
        [ForgeApp.sharedApp.viewController presentViewController:debugWarning animated:YES completion:nil];
    });
}

+ (void)hideDebugWarning:(ForgeTask*)task {
    [debugWarning dismissViewControllerAnimated:YES completion:nil];
}


@end
