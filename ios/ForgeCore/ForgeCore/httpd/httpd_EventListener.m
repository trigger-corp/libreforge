#include <sys/types.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#import "Criollo/CRResponse.h"

#import "ForgeApp.h"
#import "ForgeLog.h"
#import "ForgeStorage.h"

#import "httpd_EventListener.h"


@implementation httpd_EventListener

static ServerDelegate* delegate = nil;
static CRHTTPServer*   server = nil;
static int port = 44300;

static bool isOnLoadInitialPage = NO;
static bool isApplicationWillEnterForeground = NO;

// = Helpers ==================================================================

+ (int) findFreePort {
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_port = 0;
    inet_aton("0.0.0.0", &addr.sin_addr);
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        [ForgeLog e:@"socket() failed to find free port"];
        return 0;
    }
    if (bind(sock, (struct sockaddr*) &addr, sizeof(addr)) != 0) {
        [ForgeLog e:@"bind() failed to find free port"];
        return 0;
    }
    socklen_t len = sizeof(addr);
    if (getsockname(sock, (struct sockaddr*) &addr, &len) != 0) {
        [ForgeLog e:@"getsockname() failed to find free port"];
        return 0;
    }
    [ForgeLog d:[NSString stringWithFormat:@"Found free network port: %d", addr.sin_port]];
    return (addr.sin_port);
}


+ (NSURL*) getURL {
    NSString *url = [NSString stringWithFormat:@"https://localhost:%d/src/index.html", port];

    NSDictionary* config = [[ForgeApp.sharedApp.appConfig objectForKey:@"core"] objectForKey:@"general"];
    if ([config objectForKey:@"url"]) {
        url = [config objectForKey:@"url"];
    }

    return [NSURL URLWithString:url];
}


+ (bool) startServer {
#ifdef DEBUG_HTTPD
    NSLog(@"httpd startServer");
#endif // DEBUG_HTTPD
    if (server != nil) {
        NSLog(@"httpd startServer server already started");
        return YES;
    }

    NSError* error;

    // Get config
    NSDictionary* config = [[ForgeApp.sharedApp.appConfig objectForKey:@"core"] objectForKey:@"general"];

    // Configure port: Fixed port 5 by default, zero now chooses randomly
    port = 44300;
    if ([[config objectForKey:@"httpd"] objectForKey:@"port"]) {
        port = ((NSNumber*)[[config objectForKey:@"httpd"] objectForKey:@"port"]).intValue;
        if (port == 0) {
            port = [httpd_EventListener findFreePort];
            if (port == 0) {
                [ForgeLog e:@"Could not find a free port to start httpd on."];
                return NO;
            }
        }
    }

    // Create server
    delegate = [[ServerDelegate alloc] init];
    server   = [[CRHTTPServer alloc] initWithDelegate:delegate];

    // Configure SSL if we're using it
    NSURLComponents *components = [NSURLComponents componentsWithURL:[httpd_EventListener getURL] resolvingAgainstBaseURL:YES];
    if ([components.scheme isEqualToString:@"https"]) {
        NSBundle *coreBundle = [NSBundle bundleWithPath:[[[NSBundle mainBundle] resourcePath] stringByAppendingPathComponent:@"ForgeCore.bundle"]];
        server.isSecure = YES;
        server.identityPath = [coreBundle pathForResource:@"localhost.p12" ofType:@""];
        server.password = @"insecure";

        NSString *certificate_path     = [[config objectForKey:@"httpd"] objectForKey:@"certificate_path"];
        NSString *certificate_password = [[config objectForKey:@"httpd"] objectForKey:@"certificate_password"];
        if (certificate_path != nil && certificate_password != nil) {
            NSURL *sourceDirectory = ForgeStorage.Directories.Source;
            NSURL *certificate_url = [sourceDirectory URLByAppendingPathComponent:certificate_path];
            if ([certificate_url checkResourceIsReachableAndReturnError:&error] == YES) {
                [ForgeLog d:[NSString stringWithFormat:@"Configured httpd to use custom certificate: %@", certificate_url]];
                server.identityPath = [certificate_url path];
                server.password = certificate_password;
            } else {
                [ForgeLog e:[NSString stringWithFormat:@"Failed to specify custom certificate and password for httpd: %@", error.localizedDescription]];
                [ForgeLog e:[NSString stringWithFormat:@"Full path: %@", certificate_url]];
            }
        }
    }

    // Mount top-level paths: /assets/forge, /assets/src, /tmp
    [server mount:ForgeStorage.Endpoints.Forge     directoryAtPath:ForgeStorage.Directories.Forge.path];
    [server mount:ForgeStorage.Endpoints.Source    directoryAtPath:ForgeStorage.Directories.Source.path];
    [server mount:ForgeStorage.Endpoints.Temporary directoryAtPath:ForgeStorage.Directories.Temporary.path];
    [server mount:ForgeStorage.Endpoints.Permanent directoryAtPath:ForgeStorage.Directories.Permanent.path];
    [server mount:ForgeStorage.Endpoints.Documents directoryAtPath:ForgeStorage.Directories.Documents.path];
    
    // Start Server
    [server startListening:&error portNumber:port interface:@"loopback"];
    if (error) {
        [ForgeLog e:[NSString stringWithFormat:@"Failed to start httpd: %@", error.description]];
        server = nil;
        return NO;
    } else {
        [ForgeLog d:[NSString stringWithFormat:@"Started httpd on port: %d", port]];
    }

    return YES;
}


+ (void) stopServer {
#ifdef DEBUG_HTTPD
    NSLog(@"httpd stopServer");
#endif // DEBUG_HTTPD
    if (server == nil) {
        [ForgeLog e:@"Failed to stop httpd: Server is not initialized"];
    }
    [server stopListening];
    server = nil;
}


+ (void) restartServer {
#ifdef DEBUG_HTTPD
    NSLog(@"httpd_EventListener::restartServer");
#endif // DEBUG_HTTPD
    if (server != nil) {
        [server stopListening];
        server = nil;
        isOnLoadInitialPage = YES;
        [httpd_EventListener startServer];
    }
}


// = Life-cycle ===============================================================

+ (void)applicationWillEnterForeground:(UIApplication *)application {
#ifdef DEBUG_HTTPD
    NSLog(@"httpd applicationWillEnterForeground");
#endif // DEBUG_HTTPD
    if (server == nil) {
        [httpd_EventListener startServer];
    }
    isApplicationWillEnterForeground = YES;
}

+ (void)applicationWillResignActive:(UIApplication *)application {
#ifdef DEBUG_HTTPD
    NSLog(@"httpd applicationWillResignActive");
#endif // DEBUG_HTTPD
}

+ (void)applicationDidBecomeActive:(UIApplication *)application {
#ifdef DEBUG_HTTPD
    NSLog(@"httpd applicationDidBecomeActive");
#endif // DEBUG_HTTPD
    if (server == nil) {
        [httpd_EventListener startServer];
    }
}

+ (void)applicationDidEnterBackground:(UIApplication *)application {
#ifdef DEBUG_HTTPD
    NSLog(@"httpd applicationDidEnterBackground");
#endif // DEBUG_HTTPD
    [httpd_EventListener stopServer];
}

+ (void)applicationWillTerminate:(UIApplication *)application {
#ifdef DEBUG_HTTPD
    NSLog(@"httpd applicationWillTerminate");
#endif // DEBUG_HTTPD
    [httpd_EventListener stopServer];
}


// = onLoadInitialPage ========================================================

+ (NSNumber*) onLoadInitialPage {
    isOnLoadInitialPage = YES;
    if (![httpd_EventListener startServer]) {
        [ForgeLog e:@"Failed to start server for httpd module"];
        return @NO;
    }
    return @YES;
}

@end


// = CRServerDelegate =========================================================

@implementation ServerDelegate

- (void)serverDidStartListening:(CRServer *)server {
#ifdef DEBUG_HTTPD
    NSLog(@"httpd serverDidStartListening");
#endif // DEBUG_HTTPD

    // Handle onLoadInitialPage
    if (isOnLoadInitialPage == YES) {
        NSURLComponents *components = [NSURLComponents componentsWithURL:[httpd_EventListener getURL] resolvingAgainstBaseURL:YES];
        CRHTTPServer *crhttpserver = (CRHTTPServer*)server;
        if (crhttpserver.isSecure) {
            components.scheme = @"https";
        } else {
            components.scheme = @"http";
        }
        NSString *url = [components.URL absoluteString];

        NSDictionary *config = [[ForgeApp.sharedApp.appConfig objectForKey:@"core"] objectForKey:@"general"];
        if ([config objectForKey:@"url"]) {
            url = [config objectForKey:@"url"];
        }

        [ForgeLog d:[NSString stringWithFormat:@"Loading initial page: %@", url]];
        dispatch_async(dispatch_get_main_queue(), ^{
            [ForgeApp.sharedApp.viewController loadURL:[NSURL URLWithString: url]];
        });
        isOnLoadInitialPage = NO;
    }

    if (isApplicationWillEnterForeground == YES) {
        // TODO This is a particularly ugly hack to make sure the app can access
        //      content served by this module in the appResumed handler
        NSLog(@"httpd module started, now firing event.appResumed");
        [ForgeApp.sharedApp event:@"event.appResumed" withParam:[NSNull null]];
        isApplicationWillEnterForeground  = NO;
    }
}

- (void)serverDidStopListening:(CRServer *)s {
#ifdef DEBUG_HTTPD
    NSLog(@"httpd serverDidStopListening");
#endif // DEBUG_HTTPD
    server = nil;
}

- (void)server:(CRServer *)server didAcceptConnection:(CRConnection *)connection {
#ifdef DEBUG_HTTPD
    NSLog(@"httpd didAcceptConnection\t%lu", (unsigned long)connection.hash);
#endif // DEBUG_HTTPD
}

- (void)server:(CRServer *)server didReceiveRequest:(CRRequest *)request {
#ifdef DEBUG_HTTPD
    NSLog(@"httpd didReceiveRequest\t\t%lu %@", (unsigned long)request.connection.hash, request.URL);
#endif // DEBUG_HTTPD
}

- (void)server:(CRServer *)server didFinishRequest:(CRRequest *)request {
#ifdef DEBUG_HTTPD
    NSLog(@"httpd didFinishRequest\t\t%lu %@", (unsigned long)request.connection.hash, request.URL);
#endif // DEBUG_HTTPD
}

- (void)server:(CRServer  *)server didCloseConnection:(CRConnection *)connection {
#ifdef DEBUG_HTTPD
    NSLog(@"httpd didCloseConnection\t%lu", (unsigned long)connection.hash);
#endif // DEBUG_HTTPD
}

@end
