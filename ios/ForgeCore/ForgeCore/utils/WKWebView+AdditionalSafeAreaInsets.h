#import <Foundation/Foundation.h>
#import <WebKit/WebKit.h>

NS_ASSUME_NONNULL_BEGIN

typedef UIEdgeInsets (^SafeAreaInsetsHandler)(UIEdgeInsets insets);

@interface WKWebView (AdditionalSafeAreaInsets)
@property (nonatomic, strong) SafeAreaInsetsHandler safeAreaInsetsHandler;
- (UIEdgeInsets) safeAreaInsets;
@end

NS_ASSUME_NONNULL_END
