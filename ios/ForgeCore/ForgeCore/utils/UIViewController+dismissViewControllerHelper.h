#import <UIKit/UIKit.h>

@interface UIViewController (dismissViewControllerHelper)

- (void)dismissViewControllerHelper:(void (^)(void))completion;

@end
