#import "UIViewController+dismissViewControllerHelper.h"

@implementation UIViewController (dismissViewControllerHelper)

- (void)dismissViewControllerHelper:(void (^)(void))completion {
	if ([self respondsToSelector:@selector(dismissViewControllerAnimated:completion:)]) {
		[self dismissViewControllerAnimated:YES completion:completion];
	} else {
		[self dismissViewControllerAnimated:YES completion:nil];
		int64_t delayInSeconds = 1.0;
		dispatch_time_t popTime = dispatch_time(DISPATCH_TIME_NOW, delayInSeconds * NSEC_PER_SEC);
		dispatch_after(popTime, dispatch_get_main_queue(), completion);
	}
}

@end
