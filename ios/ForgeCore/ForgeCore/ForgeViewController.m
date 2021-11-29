#import "ForgeViewController.h"
#import "ForgeLog.h"
#import "ForgeApp.h"
#import "ForgeStorage.h"
#import "ForgeUtil.h"
#import "ForgeConstant.h"

#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wundeclared-selector"

/** Forge view controller base */
@implementation ForgeViewController


/**
 * @deprecated Use [ForgeUtil isIpad] instead.
 */
+ (BOOL)isIPad {
    return [ForgeUtil isIpad];
}


- (void)viewDidLoad {
    [super viewDidLoad];

    // Listen for keyboard events
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(keyboardWillShow:) name:UIKeyboardWillShowNotification object:nil];
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(keyboardWillHide:) name:UIKeyboardWillHideNotification object:nil];
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(keyboardDidShow:) name:UIKeyboardDidShowNotification object:nil];
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(keyboardDidHide:) name:UIKeyboardDidHideNotification object:nil];

    // Disable native UI elements by default
    _navigationBarHidden = YES;
    _tabBarHidden = YES;

    // Set default status bar style
    _statusBarStyle = UIStatusBarStyleDefault;

    // Accept cookies by default
    [[NSHTTPCookieStorage sharedHTTPCookieStorage] setCookieAcceptPolicy:NSHTTPCookieAcceptPolicyAlways];

    // Clear and configure cache
    [[NSURLCache sharedURLCache] removeAllCachedResponses];
    int cacheSizeMemory = 0;
    int cacheSizeDisk = 0;
    NSNumber *cache_enabled = [[[[ForgeApp.sharedApp.appConfig objectForKey:@"core"] objectForKey:@"general"] objectForKey:@"cache"] objectForKey:@"enabled"];
    if ([cache_enabled boolValue] == YES) {
        cacheSizeMemory = 8 * 1024 * 1024; //  8MB
        cacheSizeDisk = 32 * 1024 * 1024;  // 32MB
    }
    NSURLCache *sharedCache = [[NSURLCache alloc] initWithMemoryCapacity:cacheSizeMemory
                                                            diskCapacity:cacheSizeDisk
                                                                diskPath:@"nsurlcache"];
    [NSURLCache setSharedURLCache:sharedCache];
}


/**
 * Load a specific URL in the webView
 * @param url URL to load.
 */
- (void)loadURL:(NSURL *)url {}


+ (void)initialize {
}


- (void)didReceiveMemoryWarning {
    [super didReceiveMemoryWarning];

    // Clear cache
    [[NSURLCache sharedURLCache] removeAllCachedResponses];

    // Releases the view if it doesn't have a superview.
    [super didReceiveMemoryWarning];
    [ForgeLog w:@"App received memory warning"];
}


- (BOOL)shouldAllowRequest:(NSURLRequest *)request {
    // Called when a URL is requested
    NSURL *url = [request URL];
    [ForgeLog d:[NSString stringWithFormat:@"Evaluating request: %@", url]];

    if ([[url scheme] isEqualToString:@"forge"]) {
        return NO;
    } else if ([[url scheme] isEqualToString:@"file"]) {
        [ForgeLog d:[NSString stringWithFormat:@"Loading local url in webview: %@", [url absoluteString]]];
        return YES;
    } else if ([[url scheme] isEqualToString:@"about"]) {
        // Ignore about pages
        return NO;
    } else if (([[url scheme] isEqualToString:@"http"] || [[url scheme] isEqualToString:@"https"]) && ![[[request URL] absoluteString] isEqualToString:[[request mainDocumentURL] absoluteString]]) {
        // Allow http and https in iframes for trusted urls, otherwise allow device to handle it
        if ([self isTrustedURL:url]) {
            [ForgeLog d:[NSString stringWithFormat:@"Webview iframe switching to trusted URL: %@", [url absoluteString]]];
            return YES;
        } else {
            [self allowDeviceToHandleURL:url];
            return NO;
        }
    }

    // See if URL is trusted
    if ([self isTrustedURL:url]) {
        [ForgeLog d:[NSString stringWithFormat:@"Webview switching to trusted URL: %@", [url absoluteString]]];
        return YES;
    }

    // See if URL is a request for the live server
    NSDictionary *live = [[[ForgeApp.sharedApp.appConfig objectForKey:@"core"] objectForKey:@"general"] objectForKey:@"live"];
    if (live && [[live objectForKey:@"enabled"] boolValue]) {
        return [[url host] isEqualToString:[[NSURL URLWithString:[live objectForKey:@"url"]] host]];
    }

    // allow device to handle URL
    [self allowDeviceToHandleURL:url];
    return NO;
}


- (void) allowDeviceToHandleURL:(NSURL*) url {
    [ForgeLog d:[NSString stringWithFormat:@"Allowing device to handle external url: %@", [url absoluteString]]];
    [[UIApplication sharedApplication] openURL:url options:@{} completionHandler:nil];
}


- (BOOL) isTrustedURL:(NSURL*) url {
    if ([ForgeUtil url:[url absoluteString] matchesPattern:@"https://localhost/*"]) {
        return YES;
    } else if ([ForgeUtil url:[url absoluteString] matchesPattern:@"http://localhost/*"]) {
        return YES;
    } else if ([ForgeUtil url:[url absoluteString] matchesPattern:@"https://127.0.0.1/*"]) {
        return YES;
    } else if ([ForgeUtil url:[url absoluteString] matchesPattern:@"http://127.0.0.1/*"]) {
        return YES;
    }

    NSArray* trusted_urls = (NSArray*)[[[ForgeApp.sharedApp.appConfig objectForKey:@"core"] objectForKey:@"general"] objectForKey:@"trusted_urls"];
    for (NSString *pattern in trusted_urls) {
        if ([ForgeUtil url:[url absoluteString] matchesPattern:pattern]) {
            return YES;
        }
    }
    return NO;
}


#pragma mark - View lifecycle

/**
 * Force webView to (re)load the initial page
 */
- (void)loadInitialPage {
    hasLoaded = NO;
    [ForgeApp.sharedApp nativeEvent:@selector(preFirstWebViewLoad) withArgs:@[]];

    NSUserDefaults *prefs = [NSUserDefaults standardUserDefaults];
    // UUID to put assets in - workaround for iOS 6 caching issues
    if ([prefs objectForKey:@"reload-assets-id"] == nil) {
        NSString *uuid = (__bridge_transfer NSString *)CFUUIDCreateString(kCFAllocatorDefault, CFUUIDCreate(kCFAllocatorDefault));
        [prefs setValue:uuid forKey:@"reload-assets-id"];
        [prefs synchronize];
    }

    // If we don't have an assets folder then symlink it to the one included in the app
    if (![[NSFileManager defaultManager] fileExistsAtPath:[[ForgeApp.sharedApp assetsFolderLocationWithPrefs:prefs] path]]) {
        [self createAssetsFolderWithPrefs:prefs];
    }

    [self showInitialPageWithPrefs:prefs isRetry:NO];
}


- (void)showInitialPageWithPrefs:(NSUserDefaults*)prefs isRetry:(BOOL)isRetry {
    NSError *error = nil;
    // TODO rewrite to use ForgeFile
    NSURL *sourceDirectory = ForgeStorage.Directories.Source;
    NSURL *indexHtml = [sourceDirectory URLByAppendingPathComponent:@"index.html"];
    NSURL *realIndexHtml = [indexHtml URLByResolvingSymlinksInPath];
    NSDictionary *live = [[[ForgeApp.sharedApp.appConfig objectForKey:@"core"] objectForKey:@"general"] objectForKey:@"live"];

    // check that our assets folder is available
    if (![[NSFileManager defaultManager] fileExistsAtPath:[realIndexHtml path]]) {
        if (isRetry) {
            // first attempt to clean up should always work: really are in trouble here
            [ForgeLog e:[NSString stringWithFormat:@"Attempt to clean up assets failed: couldn't find %@ from symlink %@: %@", realIndexHtml, indexHtml, error]];
            return;
        }

        // nuke assets and retry
        [ForgeLog w:[NSString stringWithFormat:@"Couldn't find %@ from symlink %@: %@", realIndexHtml, indexHtml, error]];
        [ForgeLog w:@"Retrying..."];
        [self removeAssetsFolderWithPrefs:prefs];
        [self createAssetsFolderWithPrefs:prefs];
        [self showInitialPageWithPrefs:prefs isRetry:YES];
        return;
    }

    // check if we are in Forge "live" mode
    if (live && [[live objectForKey:@"enabled"] boolValue]) {
        [self loadURL:[NSURL URLWithString:[live objectForKey:@"url"]]];
        [ForgeLog d:[NSString stringWithFormat:@"Loading live page in webview: %@", [live objectForKey:@"url"]]];
        return;
    }

    // check if a module is handling it
    bool moduleRet = ((NSNumber*)[ForgeApp.sharedApp nativeEvent:@selector(onLoadInitialPage) withArgs:@[]]).boolValue;
    if (moduleRet) {
        [ForgeLog d:@"Loading initial page via module."];
        return;
    }

    // load from local filesystem
    [self loadURL:indexHtml];
    [ForgeLog d:@"Loading initial page in webview."];
}


- (void)createAssetsFolderWithPrefs:(NSUserDefaults*)prefs {
    NSError *error = nil;

    NSURL *assetsFolder = [ForgeApp.sharedApp assetsFolderLocationWithPrefs:prefs];
    [[NSFileManager defaultManager] createDirectoryAtURL:assetsFolder withIntermediateDirectories:YES attributes:nil error:&error];
    if (error != nil) {
        [ForgeLog e:[NSString stringWithFormat:@"failed to create directory: %@", error]];
        return;
    }

    NSURL *bundleFromAssets = ForgeApp.sharedApp.bundleLocationRelativeToAssets;
    NSURL *assetsForge = [assetsFolder URLByAppendingPathComponent:@"forge"];
    NSURL *bundleForge = [bundleFromAssets URLByAppendingPathComponent:@"assets/forge"];
    [ForgeLog d:[NSString stringWithFormat:@"creating link from %@ to %@", assetsForge, bundleForge]];
    [[NSFileManager defaultManager] createSymbolicLinkAtURL:assetsForge
                                         withDestinationURL:bundleForge
                                                       error:&error];
    if (error != nil) {
        [ForgeLog e:[NSString stringWithFormat:@"failed to create link: %@", error]];
        return;
    }

    NSURL *assetsSrc = [assetsFolder URLByAppendingPathComponent:@"src"];
    NSURL *bundleSrc = [bundleFromAssets URLByAppendingPathComponent:@"assets/src"];
    [ForgeLog d:[NSString stringWithFormat:@"creating link from %@ to %@", assetsSrc, bundleSrc]];
    [[NSFileManager defaultManager] createSymbolicLinkAtURL:assetsSrc
                                         withDestinationURL:bundleSrc
                                                       error:&error];
    if (error != nil) {
        [ForgeLog e:[NSString stringWithFormat:@"failed to create link: %@", error]];
        return;
    }
}


- (void)removeAssetsFolderWithPrefs:(NSUserDefaults*)prefs {
    NSError *error = nil;
    [[NSFileManager defaultManager] removeItemAtURL:[ForgeApp.sharedApp assetsFolderLocationWithPrefs:prefs] error:&error];
    if (error != nil) {
        [ForgeLog w:[NSString stringWithFormat:@"Problem while deleting assets folder: %@", error]];
        return;
    }
}


- (BOOL) canBecomeFirstResponder {
    return ((NSNumber*)[ForgeApp.sharedApp nativeEvent:@selector(canBecomeFirstResponder) withArgs:@[]]).boolValue;
}


- (BOOL) canResignFirstResponder {
    return ((NSNumber*)[ForgeApp.sharedApp nativeEvent:@selector(canResignFirstResponder) withArgs:@[]]).boolValue;
}


- (UIInterfaceOrientationMask)supportedInterfaceOrientations {
    if (forcePortrait) {
        return UIInterfaceOrientationMaskPortrait;
    } else {
        return ((NSNumber*)[ForgeApp.sharedApp nativeEvent:@selector(supportedInterfaceOrientations) withArgs:@[]]).integerValue;
    }
}


- (BOOL)shouldAutorotate {
    return YES;
}


- (UIViewController *)childViewControllerForStatusBarHidden {
    return self.presentedViewController;
}


- (void)dismissViewControllerAnimated:(BOOL)flag completion:(void (^)(void))completion {
    [super dismissViewControllerAnimated:flag completion:^() {
        if (floor(NSFoundationVersionNumber) > NSFoundationVersionNumber_iOS_6_1) {
            [self setNeedsStatusBarAppearanceUpdate];
        }
        if (completion != nil) {
            completion();
        }
    }];
}


- (void)presentViewController:(UIViewController *)viewControllerToPresent animated:(BOOL)flag completion:(void (^)(void))completion {
    [super presentViewController:viewControllerToPresent animated:flag completion:^() {
        if (floor(NSFoundationVersionNumber) > NSFoundationVersionNumber_iOS_6_1) {
            [self setNeedsStatusBarAppearanceUpdate];
        }
        if (completion != nil) {
            completion();
        }
    }];
}


- (void)willTransitionToTraitCollection:(UITraitCollection *)newCollection
              withTransitionCoordinator:(id<UIViewControllerTransitionCoordinator>)coordinator {
    [super willTransitionToTraitCollection:newCollection withTransitionCoordinator:coordinator];
    [ForgeApp.sharedApp nativeEvent:@selector(willTransitionToTraitCollection:withTransitionCoordinator:) withArgs:@[newCollection, coordinator]];
}


#pragma mark - View Layout

- (BOOL)prefersStatusBarHidden {
    NSNumber* hidden = [ForgeApp.sharedApp nativeEvent:@selector(prefersStatusBarHidden) withArgs:@[]];
    if (hidden != nil) {
        return hidden.boolValue;
    }
    return self.statusBarHidden;
}


- (UIStatusBarStyle)preferredStatusBarStyle {
    NSNumber* style = ((NSNumber*)[ForgeApp.sharedApp nativeEvent:@selector(preferredStatusBarStyle) withArgs:@[]]);
    if (style != nil) {
        return style.intValue;
    }
    return self.statusBarStyle;
}


- (void)viewWillTransitionToSize:(CGSize)size withTransitionCoordinator:(id<UIViewControllerTransitionCoordinator>)coordinator {
    [super viewWillTransitionToSize:size withTransitionCoordinator:coordinator];

    // refresh content insets once rotation is complete
    /* TODO delete this: [coordinator animateAlongsideTransition:nil completion:^(id<UIViewControllerTransitionCoordinatorContext>  _Nonnull context) {
        UIEdgeInsets insets = UIEdgeInsetsMake(0, 0, 0, 0);
        if (@available(iOS 11.0, *)) {
            insets = self.view.safeAreaInsets; // currently this only matters for the iPhone-X
        }
        // NSLog(@"ForgeViewController::viewWillTransitionToSize insets: top=%f bottom=%f left=%f right=%f", insets.top, insets.bottom, insets.left, insets.right);
        [self setLeftInset:insets.left];
        [self setRightInset:insets.right];
        [self updateContentInsets];
    }];*/

    [ForgeApp.sharedApp nativeEvent:@selector(viewWillTransitionToSize:withTransitionCoordinator:) withArgs:@[[NSValue valueWithCGSize:size], coordinator]];
}


- (void)createStatusBarVisualEffect:(WKWebView*)theWebView {
    // remove existing status bar blur effect
    [_navigationBar setBackgroundImage:[[UIImage alloc] init] forBarMetrics:UIBarMetricsDefault];
    [_navigationBar setShadowImage:[[UIImage alloc] init]];

    // create a replacement blur effect that covers both the status bar and navigation bar
    _blurView = [[UIView alloc] init];
    _blurView.userInteractionEnabled = NO;
    _blurView.backgroundColor = [UIColor clearColor];
    _blurViewVisualEffect = [[UIVisualEffectView alloc] initWithEffect:[UIBlurEffect effectWithStyle:UIBlurEffectStyleRegular]];
    _blurViewVisualEffect.userInteractionEnabled = NO;
    [_blurView addSubview:_blurViewVisualEffect];
    [self.view insertSubview:_blurView aboveSubview:theWebView];

    // layout constraints
    _blurViewBottomConstraint = [NSLayoutConstraint constraintWithItem:_blurView
                                                            attribute:NSLayoutAttributeBottom
                                                            relatedBy:NSLayoutRelationEqual
                                                               toItem:self.view.safeAreaLayoutGuide
                                                            attribute:NSLayoutAttributeTop
                                                           multiplier:1.0f
                                                             constant:0.0f];

    _blurViewBottomConstraint_with_navigationBar  = [NSLayoutConstraint constraintWithItem:_blurView
                                                               attribute:NSLayoutAttributeBottom
                                                               relatedBy:NSLayoutRelationEqual
                                                                  toItem:_navigationBar
                                                               attribute:NSLayoutAttributeBottom
                                                              multiplier:1.0f
                                                                constant:0.0f];

    [self layoutStatusBarVisualEffect];
}


- (void)layoutStatusBarVisualEffect {
    _blurView.translatesAutoresizingMaskIntoConstraints = NO;
    [_blurView.leadingAnchor constraintEqualToAnchor:self.view.leadingAnchor].active = YES;
    [_blurView.trailingAnchor constraintEqualToAnchor:self.view.trailingAnchor].active = YES;
    [_blurView.topAnchor constraintEqualToAnchor:self.view.topAnchor].active = YES;

    if (_navigationBarHidden == YES) {
        _blurViewBottomConstraint.active = YES;
        _blurViewBottomConstraint_with_navigationBar.active = NO;
    } else {
        _blurViewBottomConstraint.active = NO;
        _blurViewBottomConstraint_with_navigationBar.active = YES;
    }

    _blurViewVisualEffect.translatesAutoresizingMaskIntoConstraints = NO;
    [_blurViewVisualEffect.leadingAnchor constraintEqualToAnchor:_blurView.leadingAnchor].active = YES;
    [_blurViewVisualEffect.trailingAnchor constraintEqualToAnchor:_blurView.trailingAnchor].active = YES;
    [_blurViewVisualEffect.topAnchor constraintEqualToAnchor:_blurView.topAnchor].active = YES;
    [_blurViewVisualEffect.bottomAnchor constraintEqualToAnchor:_blurView.bottomAnchor].active = YES;
}


- (void)setStatusBarHidden:(BOOL)hidden {
    _statusBarHidden = hidden;
    [ForgeApp.sharedApp.viewController setNeedsStatusBarAppearanceUpdate];
}


- (void)setStatusBarTransparent:(BOOL)transparent {
    _statusBarTransparent = transparent;
    [_blurView setHidden:transparent];
}


- (void)setStatusBarStyle:(UIStatusBarStyle)style {
    if (@available(iOS 13.0, *)) {
        if (style == UIStatusBarStyleLightContent) {
            _statusBarStyle = UIStatusBarStyleLightContent;
            _navigationBar.titleTextAttributes = [NSDictionary dictionaryWithObject:[UIColor whiteColor] forKey:NSForegroundColorAttributeName];
        } else if (style == UIStatusBarStyleDarkContent) {
            _statusBarStyle = UIStatusBarStyleDarkContent;
            _navigationBar.titleTextAttributes = [NSDictionary dictionaryWithObject:[UIColor blackColor] forKey:NSForegroundColorAttributeName];
        }  else {
            _statusBarStyle = UIStatusBarStyleDefault;
            _navigationBar.titleTextAttributes = [NSDictionary dictionaryWithObject:[UIColor blackColor] forKey:NSForegroundColorAttributeName];
        }
    } else {
        if (style == UIStatusBarStyleLightContent) {
            _statusBarStyle = UIStatusBarStyleLightContent;
            _navigationBar.titleTextAttributes = [NSDictionary dictionaryWithObject:[UIColor whiteColor] forKey:NSForegroundColorAttributeName];
        } else {
            _statusBarStyle = UIStatusBarStyleDefault;
            _navigationBar.titleTextAttributes = [NSDictionary dictionaryWithObject:[UIColor blackColor] forKey:NSForegroundColorAttributeName];
        }
    }

    [ForgeApp.sharedApp.viewController setNeedsStatusBarAppearanceUpdate];
}


- (void)setNavigationBarHidden:(BOOL)hidden {
    [_navigationBar setHidden:hidden];
    _navigationBarHidden = hidden;
    [self layoutStatusBarVisualEffect];
    [self forceUpdateWebView];
}


- (void)setTabBarHidden:(BOOL)hidden {
    [_tabBar setHidden:hidden];
    _tabBarHidden = hidden;
    [self forceUpdateWebView];
}


- (void)updateContentInsets {
    self.navigationBarHidden = _navigationBarHidden;
    self.tabBarHidden = _tabBarHidden;
}


- (void) forceUpdateWebView {
}


- (void)keyboardWillShow:(NSNotification*)notification {
    [ForgeApp.sharedApp nativeEvent:@selector(keyboardWillShow:) withArgs:@[notification]];
}

- (void)keyboardWillHide:(NSNotification*)notification {
    [ForgeApp.sharedApp nativeEvent:@selector(keyboardWillHide:) withArgs:@[notification]];
}

- (void)keyboardDidShow:(NSNotification*)notification {
    [ForgeApp.sharedApp nativeEvent:@selector(keyboardDidShow:) withArgs:@[notification]];
}

- (void)keyboardDidHide:(NSNotification*)notification {
    [ForgeApp.sharedApp nativeEvent:@selector(keyboardDidHide:) withArgs:@[notification]];
}

@end

#pragma clang diagnostic pop
