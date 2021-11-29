#import <objc/runtime.h>

#import "WKWebView+AdditionalSafeAreaInsets.h"


@implementation WKWebView (AdditionalSafeAreaInsets)

- (SafeAreaInsetsHandler)safeAreaInsetsHandler {
    return objc_getAssociatedObject(self, @selector(safeAreaInsetsHandler));
}


- (void)setSafeAreaInsetsHandler:(SafeAreaInsetsHandler)handler {
    objc_setAssociatedObject(self, @selector(safeAreaInsetsHandler), handler, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
}


- (UIEdgeInsets) safeAreaInsets {
    SafeAreaInsetsHandler safeAreaInsetsHandler = self.safeAreaInsetsHandler;
    if (safeAreaInsetsHandler != NULL) {
        return safeAreaInsetsHandler(super.safeAreaInsets);
    }
    return super.safeAreaInsets;
}

@end

