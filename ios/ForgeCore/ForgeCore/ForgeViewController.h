#import <WebKit/WebKit.h>

@interface ForgeViewController : UIViewController {
	BOOL hasLoaded;
	@public BOOL forcePortrait;

    UIView *_blurView;
    UIVisualEffectView *_blurViewVisualEffect;
    NSLayoutConstraint *_blurViewBottomConstraint;
    NSLayoutConstraint *_blurViewBottomConstraint_with_navigationBar;

    IBOutlet UINavigationBar *_navigationBar;
    IBOutlet UITabBar *_tabBar;

    UIStatusBarStyle _statusBarStyle;
    BOOL _statusBarHidden;
    BOOL _statusBarTransparent;

    BOOL _navigationBarHidden;
    BOOL _tabBarHidden;

    NSLayoutConstraint *_navigationBarTopConstraint;
    NSLayoutConstraint *_tabBarBottomConstraint;

    IBOutlet UIView *view;
    IBOutlet WKWebView *webView;
}

@property (nonatomic) UIStatusBarStyle statusBarStyle;
@property (nonatomic) BOOL statusBarHidden;
@property (nonatomic) BOOL statusBarTransparent;

@property (nonatomic) BOOL navigationBarHidden;
@property (nonatomic) BOOL tabBarHidden;

@property (readonly) UINavigationBar *navigationBar;
@property (readonly) UITabBar *tabBar;
@property (readonly) UIView *blurView;
@property (readonly) UIVisualEffectView *blurViewVisualEffect;

- (void)loadInitialPage;
- (void)loadURL:(NSURL*)url;
- (BOOL)shouldAllowRequest:(NSURLRequest *)request;
- (BOOL)isTrustedURL:(NSURL*) url;
- (void) allowDeviceToHandleURL:(NSURL*) url;

- (void)createStatusBarVisualEffect:(WKWebView*)theWebView;

- (void)setStatusBarHidden:(BOOL)hidden;
- (void)setStatusBarTransparent:(BOOL)hidden;
- (void)setStatusBarStyle:(UIStatusBarStyle)style;
- (void)setNavigationBarHidden:(BOOL)hidden;
- (void)setTabBarHidden:(BOOL)hidden;

- (void)updateContentInsets;
- (void)forceUpdateWebView;

- (void)keyboardWillShow:(NSNotification*)notification;
- (void)keyboardWillHide:(NSNotification*)notification;
- (void)keyboardDidShow:(NSNotification*)notification;
- (void)keyboardDidHide:(NSNotification*)notification;

@property (class, nonatomic, assign, readonly) BOOL isIPad; // @deprecated

// so we can get these in iOS < 11 as well
typedef NS_ENUM(NSInteger, ForgeContentInsetAdjustmentBehavior) {
    ForgeContentInsetAdjustmentAutomatic,      // Not supported - behaves like "Never"
    ForgeContentInsetAdjustmentScrollableAxes, // Not supported - behaves like "Never"
    ForgeContentInsetAdjustmentNever,          // contentInset is not adjusted
    ForgeContentInsetAdjustmentAlways,         // contentInset is always adjusted by the scroll view's safeAreaInsets
};

@end
