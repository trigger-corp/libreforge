#import "WKWebViewController.h"
#import "BorderControl.h"
#import "ForgeLog.h"
#import "ForgeApp.h"
#import "ForgeUtil.h"
#import "ForgeConstant.h"

#import "WKWebView+AdditionalSafeAreaInsets.h"

#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wundeclared-selector"


@implementation WKWebViewController

#pragma mark - View lifecycle

- (void)viewDidLoad {
    hasLoaded = NO;
    [super viewDidLoad];

    WKWebViewConfiguration* configuration = [[WKWebViewConfiguration alloc] init];

    // create a global WKProcessPool
    configuration.processPool = [[WKProcessPool alloc] init];

    // add script message handler
    [configuration.userContentController addScriptMessageHandler:self name:@"forge"];

    // configure WebView default behaviors
    configuration.allowsInlineMediaPlayback = YES;
    configuration.mediaTypesRequiringUserActionForPlayback = WKAudiovisualMediaTypeNone;

    // configure WebView preferences
    configuration.preferences.minimumFontSize = 1.0;
    configuration.preferences.javaScriptCanOpenWindowsAutomatically = YES;
    configuration.preferences.javaScriptEnabled = YES;

    // Workaround CORS errors when using file:/// also see: https://bugs.webkit.org/show_bug.cgi?id=154916
    // TODO drop support for these. Everything should come via the webserver.
    @try {
        [configuration.preferences setValue:@TRUE forKey:@"allowFileAccessFromFileURLs"];
    } @catch (NSException *exception) {}
    @try {
        [configuration setValue:@TRUE forKey:@"allowUniversalAccessFromFileURLs"];
    } @catch (NSException *exception) {}

    // TODO add observer for cookiesDidChangeInCookieStore so we can set cookies in iFrame
    if (@available(iOS 11.0, *)) {
        [configuration.websiteDataStore.httpCookieStore addObserver:self];
    } else {
        // not supported
    }

    // allow modules to set configuration
    [ForgeApp.sharedApp nativeEvent:@selector(applicationWillConfigureWebView:) withArgs:@[configuration]];

    // recreate WebView with configuration
    [self recreateWebViewWithConfiguration:configuration];

    // install SafeAreaInsets handler
    __unsafe_unretained typeof(self) weakSelf = self;
    static NSString *updateInsets = @"var root = document.documentElement;"
        "root.style.setProperty('--safe-area-inset-top', '%fpx');"
        "root.style.setProperty('--safe-area-inset-right', '%fpx');"
        "root.style.setProperty('--safe-area-inset-bottom', '%fpx');"
        "root.style.setProperty('--safe-area-inset-left', '%fpx');";
    webView.safeAreaInsetsHandler = ^UIEdgeInsets(UIEdgeInsets insets) {
        if (ForgeApp.sharedApp.viewController.navigationBarHidden == NO) {
            insets.top += ForgeConstant.navigationBarHeightDynamic;
        }
        if (ForgeApp.sharedApp.viewController.tabBarHidden == NO) {
            insets.bottom += ForgeConstant.tabBarHeightDynamic;
        }
        if ([ForgeApp.sharedApp flag:@"ios_also_set_css_safe_area_inset_env_as_var"]) {
            NSString *script = [NSString stringWithFormat:updateInsets, insets.top, insets.right, insets.bottom, insets.left];
            [weakSelf->webView evaluateJavaScript:script completionHandler:nil];
        }
        return insets;
    };

    // hook webView up
    webView.UIDelegate = self;
    webView.navigationDelegate = self;
    webView.opaque = NO;
    webView.backgroundColor = [UIColor clearColor];

    // Associate webView with app
    [ForgeApp.sharedApp setWebView:webView];

    // Set overscroll behaviour
    NSNumber *bounces = [[[ForgeApp.sharedApp.appConfig objectForKey:@"core"] objectForKey:@"ios"] objectForKey:@"bounces"];
    if (bounces != nil) {
        [webView.scrollView setBounces:[bounces boolValue]];
    } else {
        [webView.scrollView setBounces:NO];
    }

    // debug bounds
    //webView.layer.borderWidth = 1;
    //webView.layer.borderColor = [UIColor greenColor].CGColor;

    // setup native elements
    [self setNavigationBarHidden:YES];
    [self setTabBarHidden:YES];
    [self createStatusBarVisualEffect:webView];

    // Load the app url
    if ([[NSBundle mainBundle] pathForResource:@"assets/src/index.html" ofType:@""] != nil) {
        [self loadInitialPage];
    } else {
        UIAlertController *alert =
            [UIAlertController alertControllerWithTitle:@"Error"
                                                message:@"No index.html found in app. Mobile apps require an index.html."
                                         preferredStyle:UIAlertControllerStyleAlert];
        [alert addAction:[UIAlertAction actionWithTitle:@"OK"
                                                  style:UIAlertActionStyleDefault
                                                handler:nil]];
        dispatch_async(dispatch_get_main_queue(), ^{
            [super presentViewController:alert animated:YES completion:nil];
        });
    }
}


// There's an issue where the interface-builder created WKWebView refuses to recognize a custom WKURLSchemeHandler
- (void) recreateWebViewWithConfiguration:(WKWebViewConfiguration*)configuration {
    [webView removeFromSuperview];

    webView = [[WKWebView alloc] initWithFrame:self.view.bounds configuration:configuration];

    [self.view insertSubview:webView belowSubview:_navigationBar];
    [self.view sendSubviewToBack:webView];

    webView.translatesAutoresizingMaskIntoConstraints = NO;
    [webView.leadingAnchor constraintEqualToAnchor:self.view.leadingAnchor].active = YES;
    [webView.trailingAnchor constraintEqualToAnchor:self.view.trailingAnchor].active = YES;
    [webView.topAnchor constraintEqualToAnchor:self.view.topAnchor].active = YES;
    [webView.bottomAnchor constraintEqualToAnchor:self.view.bottomAnchor].active = YES;

    [ForgeApp.sharedApp setWebView:webView];
}


#pragma mark - WKScriptMessageHandler

- (void)userContentController:(WKUserContentController *)userContentController didReceiveScriptMessage:(WKScriptMessage *)message {
    if (![message.name isEqualToString:@"forge"]) {
        [ForgeLog d:[NSString stringWithFormat:@"Unknown native call: %@ -> %@", message.name, message.body]];
        return;
    }
    [ForgeLog d:[NSString stringWithFormat:@"Native call: %@", message.body]];
    [BorderControl runTask:message.body forWebView:webView];
}


#pragma mark - WKNavigationDelegate

- (void)webView:(WKWebView *)webView decidePolicyForNavigationAction:(WKNavigationAction *)navigationAction decisionHandler:(void (^)(WKNavigationActionPolicy))decisionHandler {
    return [self shouldAllowRequest:navigationAction.request]
        ? decisionHandler(WKNavigationActionPolicyAllow)
        : decisionHandler(WKNavigationActionPolicyCancel);
}


- (void)webView:(WKWebView *)webView didFailProvisionalNavigation:(WKNavigation *)navigation withError:(NSError *)error {
    [ForgeLog w:[NSString stringWithFormat:@"Webview error: %@", error]];
}


- (void)webView:(WKWebView *)webView didFailNavigation:(WKNavigation *)navigation withError:(NSError *)error {
    [ForgeLog w:[NSString stringWithFormat:@"Webview error: %@", error]];
}


- (void)webView:(WKWebView *)webView didFinishNavigation:(WKNavigation *)navigation {
    if (hasLoaded == NO) {
        // First webview load
        [ForgeApp.sharedApp nativeEvent:@selector(firstWebViewLoad) withArgs:@[]];
    }
    hasLoaded = YES;
}


- (void)webView:(WKWebView *)webView didReceiveAuthenticationChallenge:(NSURLAuthenticationChallenge *)challenge completionHandler:(void (^)(NSURLSessionAuthChallengeDisposition disposition, NSURLCredential *credential))completionHandler {
    // support self-signed certificates for localhost
    if ([challenge.protectionSpace.authenticationMethod isEqualToString:NSURLAuthenticationMethodServerTrust] &&
        ([challenge.protectionSpace.host isEqualToString:@"localhost"] || [challenge.protectionSpace.host isEqualToString:@"127.0.0.1"])) {
        NSURLCredential * credential = [[NSURLCredential alloc] initWithTrust:[challenge protectionSpace].serverTrust];
        [ForgeLog d:@"[FORGE WebView] Trusting self-signed certificate for localhost"];
        completionHandler(NSURLSessionAuthChallengeUseCredential, credential);

    } else {
        completionHandler(NSURLSessionAuthChallengePerformDefaultHandling, nil);
    }
}


#pragma mark - WKHTTPCookieStoreObserver

- (void)cookiesDidChangeInCookieStore:(WKHTTPCookieStore *)cookieStore {
    NSLog(@"WKWebViewController::cookiesDidChangeInCookieStore -> %@", cookieStore);
}


#pragma mark - ForgeViewController

/**
 * Load a specific URL in the webView
 * @param url URL to load.
 */
- (void)loadURL:(NSURL *)url {
    [super loadURL:url];

    if (url.isFileURL) {
        [ForgeLog d:[NSString stringWithFormat:@"WKWebViewController::loadURL -> file -> %@", url]];
        NSError *error = nil;
        [url checkResourceIsReachableAndReturnError:&error];
        if (error != nil) {
            [ForgeLog e:[error localizedDescription]];
            return;
        }

        NSURL *restrictPath = [NSURL fileURLWithPath:@"/" isDirectory:YES];
        [ForgeLog d:[NSString stringWithFormat:@"WKWebViewController::loadURL %@ -> restricting file access to -> %@", url, restrictPath]];
        [webView loadFileURL:url allowingReadAccessToURL:restrictPath];

    } else {
        [ForgeLog d:[NSString stringWithFormat:@"WKWebViewController::loadURL -> other -> %@", url]];
        NSURLRequest *request = [NSURLRequest requestWithURL:url
                                                 cachePolicy:NSURLRequestReloadIgnoringLocalAndRemoteCacheData
                                             timeoutInterval:10];
        [webView loadRequest:request];
    }
}

// Workaround for a bug where we need to force a redraw when keyboard is hidden to expand the webview to its view again
- (void)keyboardWillHide:(NSNotification*)notification {
    [self forceUpdateWebView];
    [super keyboardWillHide:notification];
}

- (void)forceUpdateWebView {
    CGRect f = webView.frame;
    webView.frame = CGRectMake(f.origin.x, f.origin.y, f.size.width + 1, f.size.height + 1);
    webView.frame = f;
}

// Workaround for: https://github.com/trigger-corp/forge/issues/30
- (void)presentViewController:(UIViewController *)viewControllerToPresent animated:(BOOL)flag completion:(void (^)(void))completion {
    if ([viewControllerToPresent isKindOfClass:UIImagePickerController.class]) {
        viewControllerToPresent.modalPresentationStyle = UIModalPresentationCustom;
    }
    [super presentViewController:viewControllerToPresent animated:flag completion:completion];
}


#pragma mark WKUIDelegate

- (void)webView:(WKWebView *)webView runJavaScriptAlertPanelWithMessage:(NSString *)message initiatedByFrame:(WKFrameInfo *)frame completionHandler:(void (^)(void))completionHandler {
    UIAlertController *alert = [UIAlertController alertControllerWithTitle:nil
                                                                   message:message
                                                            preferredStyle:UIAlertControllerStyleAlert];
    [alert addAction:[UIAlertAction actionWithTitle:NSLocalizedString(@"OK", nil) style:UIAlertActionStyleCancel handler:^(UIAlertAction *action) {
        completionHandler();
    }]];

    [self presentViewController:alert animated:YES completion:nil];
}


- (void)webView:(WKWebView *)webView runJavaScriptConfirmPanelWithMessage:(NSString *)message initiatedByFrame:(WKFrameInfo *)frame completionHandler:(void (^)(BOOL result))completionHandler {
    UIAlertController *alert = [UIAlertController alertControllerWithTitle:nil
                                                                   message:message
                                                            preferredStyle:UIAlertControllerStyleAlert];
    [alert addAction:[UIAlertAction actionWithTitle:NSLocalizedString(@"Cancel", nil) style:UIAlertActionStyleCancel handler:^(UIAlertAction *action) {
        completionHandler(NO);
    }]];
    [alert addAction:[UIAlertAction actionWithTitle:NSLocalizedString(@"OK", nil) style:UIAlertActionStyleDefault handler:^(UIAlertAction *action) {
        completionHandler(YES);
    }]];

    [self presentViewController:alert animated:YES completion:nil];
}

- (void)webView:(WKWebView *)webView runJavaScriptTextInputPanelWithPrompt:(NSString *)prompt defaultText:(NSString *)defaultText initiatedByFrame:(WKFrameInfo *)frame completionHandler:(void (^)(NSString *result))completionHandler {
    UIAlertController *alert = [UIAlertController alertControllerWithTitle:nil
                                                                   message:prompt
                                                            preferredStyle:UIAlertControllerStyleAlert];
    [alert addTextFieldWithConfigurationHandler:^(UITextField *textField) {
        textField.placeholder = prompt;
        textField.secureTextEntry = NO;
        textField.text = defaultText;
    }];
    [alert addAction:[UIAlertAction actionWithTitle:NSLocalizedString(@"Cancel", nil) style:UIAlertActionStyleCancel handler:^(UIAlertAction *action) {
        completionHandler(nil);
    }]];
    [alert addAction:[UIAlertAction actionWithTitle:NSLocalizedString(@"OK", nil) style:UIAlertActionStyleDefault handler:^(UIAlertAction *action) {
        completionHandler([alert.textFields.firstObject text]);
    }]];

    [self presentViewController:alert animated:YES completion:nil];
}

@end

#pragma clang diagnostic pop
