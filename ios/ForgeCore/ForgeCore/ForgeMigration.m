#import "ForgeMigration.h"
#import "ForgeApp.h"

@implementation ForgeMigration


+ (NSURL*)OldWebViewStorageRoot
{
    return [ForgeApp.sharedApp.applicationSupportDirectory URLByAppendingPathComponent:@"webkit"];
}

+ (NSURL*)OldLocalStorageDir
{
    return ForgeMigration.OldWebViewStorageRoot;
}

+ (NSURL*)OldWebSQLDir
{
    return ForgeMigration.OldWebViewStorageRoot;
}

+ (NSURL*)OldIndexedDBDir
{
    return [ForgeMigration.OldWebViewStorageRoot URLByAppendingPathComponent:@"___IndexedDB"];
}


+ (NSURL*)WKWebViewStorageRoot
{
    NSError *error = nil;
    NSURL *url = [[NSFileManager defaultManager] URLForDirectory:NSLibraryDirectory inDomain:NSUserDomainMask appropriateForURL:nil create:NO error:&error];
    if (error != nil) {
        NSLog(@"Error getting WKWebViewStorageDirectory: %@", error.localizedDescription);
    }

    url = [url URLByAppendingPathComponent:@"WebKit"];
    #if TARGET_IPHONE_SIMULATOR
        NSString *bundleIdentifier = [[NSBundle mainBundle] bundleIdentifier];
        url = [url URLByAppendingPathComponent:bundleIdentifier];
    #endif
    url = [url URLByAppendingPathComponent:@"WebsiteData"];
    return url;
}

+ (NSURL*)WKLocalStorageDir
{
    return [ForgeMigration.WKWebViewStorageRoot URLByAppendingPathComponent:@"LocalStorage"];
}

+ (NSURL*)WKWebSQLDir
{
    return [ForgeMigration.WKWebViewStorageRoot URLByAppendingPathComponent:@"WebSQL"];
}

+ (NSURL*)WKIndexedDBDir
{
    return [ForgeMigration.WKWebViewStorageRoot URLByAppendingPathComponent:@"IndexedDB"];
}


// - WKWebView => OldWebView ----------------------------------------------------

+ (void)MoveWKWebViewStorageToOldWebView
{
    NSError *error = nil;
    NSFileManager* fm = [NSFileManager defaultManager];

    // create directories if needed
    if (![ForgeMigration.OldIndexedDBDir checkResourceIsReachableAndReturnError:&error]) {
        [fm createDirectoryAtURL:ForgeMigration.OldIndexedDBDir withIntermediateDirectories:YES attributes:nil error:&error];
    }

    // Localstorage
    NSArray *urls = [fm contentsOfDirectoryAtURL:ForgeMigration.WKLocalStorageDir
                      includingPropertiesForKeys:@[]
                                         options:0
                                           error:&error];
    for (NSURL *url in urls) {
        NSError *error = nil;
        NSString *name = url.lastPathComponent;
        if ([name hasSuffix:@".localstorage"] || [name hasSuffix:@".localstorage-shm"] || [name hasSuffix:@".localstorage-wal"]) {
            NSLog(@"\tsync localstorage: %@", url.lastPathComponent);
            [ForgeMigration moveItemAtURL:url toURL:[ForgeMigration.OldLocalStorageDir URLByAppendingPathComponent:name] error:&error];

        }
        if (error != nil) {
            NSLog(@"ForgeStorage::MoveWKWebViewStorageToOldWebView Error: %@", [error localizedDescription]);
        }
    }

    // WebSQL
    urls = [fm contentsOfDirectoryAtURL:ForgeMigration.WKWebSQLDir
             includingPropertiesForKeys:@[]
                                options:0
                                  error:&error];
    for (NSURL *url in urls) {
        NSError *error = nil;
        NSString *name = url.lastPathComponent;
        if ([name hasPrefix:@"Databases.db"] || [name hasPrefix:@"file_"]|| [name hasPrefix:@"http_"] || [name hasPrefix:@"https_"]) {
            NSLog(@"\tsync websql: %@", url.lastPathComponent);
            [ForgeMigration moveItemAtURL:url toURL:[ForgeMigration.OldWebSQLDir URLByAppendingPathComponent:name] error:&error];
        }
        if (error != nil) {
            NSLog(@"ForgeStorage::MoveWKWebViewStorageToOldWebView Error: %@", [error localizedDescription]);
        }
    }

    // IndexedDB
    urls = [fm contentsOfDirectoryAtURL:ForgeMigration.WKIndexedDBDir
             includingPropertiesForKeys:@[]
                                options:0
                                  error:&error];
    for (NSURL *url in urls) {
        NSError *error = nil;
        NSString *name = url.lastPathComponent;
        if ([name hasPrefix:@"file_"]|| [name hasPrefix:@"http_"] || [name hasPrefix:@"https_"]) {
            NSLog(@"\tsync indexeddb: %@", url.lastPathComponent);
            [ForgeMigration moveItemAtURL:url toURL:[ForgeMigration.OldIndexedDBDir URLByAppendingPathComponent:name] error:&error];
        }
        if (error != nil) {
            NSLog(@"ForgeStorage::MoveWKWebViewStorageToOldWebView Error: %@", [error localizedDescription]);
        }
    }
}


// - OldWebView => WKWebView ----------------------------------------------------

+ (void)MoveOldWebViewStorageToWKWebView
{
    NSError *error = nil;
    NSFileManager* fm = [NSFileManager defaultManager];

    // create directories if needed
    if (![ForgeMigration.WKLocalStorageDir checkResourceIsReachableAndReturnError:&error]) {
        [fm createDirectoryAtURL:ForgeMigration.WKLocalStorageDir withIntermediateDirectories:YES attributes:nil error:&error];
    }
    if (![ForgeMigration.WKWebSQLDir checkResourceIsReachableAndReturnError:&error]) {
        [fm createDirectoryAtURL:ForgeMigration.WKWebSQLDir withIntermediateDirectories:YES attributes:nil error:&error];
    }
    if (![ForgeMigration.WKIndexedDBDir checkResourceIsReachableAndReturnError:&error]) {
        [fm createDirectoryAtURL:ForgeMigration.WKIndexedDBDir withIntermediateDirectories:YES attributes:nil error:&error];
    }

    // LocalStorage and WebSQL
    NSArray *urls = [fm contentsOfDirectoryAtURL:ForgeMigration.OldWebViewStorageRoot
                      includingPropertiesForKeys:@[]
                                         options:0
                                           error:&error];
    for (NSURL *url in urls) {
        NSError *error = nil;
        NSString *name = url.lastPathComponent;
        if ([name hasSuffix:@".localstorage"] || [name hasSuffix:@".localstorage-shm"] || [name hasSuffix:@".localstorage-wal"]) {
            NSLog(@"\tsync localstorage: %@", url.lastPathComponent);
            [ForgeMigration moveItemAtURL:url toURL:[ForgeMigration.WKLocalStorageDir URLByAppendingPathComponent:name] error:&error];

        } else if ([name hasPrefix:@"Databases.db"] || [name hasPrefix:@"file_"]|| [name hasPrefix:@"http_"] || [name hasPrefix:@"https_"]) {
            NSLog(@"\tsync websql: %@", url.lastPathComponent);
            [ForgeMigration moveItemAtURL:url toURL:[ForgeMigration.WKWebSQLDir URLByAppendingPathComponent:name] error:&error];
        }
        if (error != nil) {
            NSLog(@"ForgeStorage::MoveOldWebViewStorageToWKWebView Error: %@", [error localizedDescription]);
        }
    }

    // IndexedDB
    urls = [fm contentsOfDirectoryAtURL:ForgeMigration.OldIndexedDBDir
                      includingPropertiesForKeys:@[]
                                         options:0
                                           error:&error];
    for (NSURL *url in urls) {
        NSError *error = nil;
        NSString *name = url.lastPathComponent;
        if ([name hasPrefix:@"file_"]|| [name hasPrefix:@"http_"] || [name hasPrefix:@"https_"]) {
            NSLog(@"\tsync indexeddb: %@", url.lastPathComponent);
            [ForgeMigration moveItemAtURL:url toURL:[ForgeMigration.WKIndexedDBDir URLByAppendingPathComponent:name] error:&error];
        }
        if (error != nil) {
            NSLog(@"ForgeStorage::MoveOldWebViewStorageToWKWebView Error: %@", [error localizedDescription]);
        }
    }
}


// - file:/// => http://localhost:port/ ----------------------------------------

+ (void)MoveFileSchemeStorageToHttpScheme {
    NSDictionary *httpd = [ForgeApp.sharedApp configForModule:@"httpd"];
    if (httpd == nil || ([httpd objectForKey:@"disabled"] != nil && [[httpd objectForKey:@"disabled"] boolValue] == YES)) {
        NSLog(@"ForgeTask::MoveFileSchemeStorageToHttpScheme only supports migration to http or https scheme");
        return;
    }
    int port = [httpd objectForKey:@"port"] ? ((NSNumber*)[httpd objectForKey:@"port"]).intValue : 0;
    if (port == 0) {
        NSLog(@"ForgeTask::MoveFileSchemeStorageToHttpScheme only supports migration to a fixed port");
        return;
    }
    NSString *protocol = [httpd objectForKey:@"certificate_path"] ? @"https" : @"http";
    NSLog(@"ForgeTask::MoveFileSchemeStorageToHttpScheme migrating file:/// storage to %@://localhost:%d/", protocol, port);

    NSURL *localStorageDir = ForgeMigration.WKLocalStorageDir;
    NSURL *indexedDBDir = ForgeMigration.WKIndexedDBDir;
    NSURL *webSQLDir = ForgeMigration.WKWebSQLDir;
    NSError *error = nil;

    // Localstorage
    NSString *sourcePrefix = @"file__0";
    NSString *destinationPrefix = [NSString stringWithFormat:@"%@_localhost_%d", protocol, port];
    for (NSString *postfix in @[@"localstorage", @"localstorage-shm", @"localstorage-wal"]) {
        NSURL *source = [localStorageDir URLByAppendingPathComponent:[NSString stringWithFormat:@"%@.%@", sourcePrefix, postfix]];
        if (![source checkResourceIsReachableAndReturnError:&error]) {
            continue;
        }
        NSURL *destination = [localStorageDir URLByAppendingPathComponent:[NSString stringWithFormat:@"%@.%@", destinationPrefix, postfix]];
        [ForgeMigration moveItemAtURL:source toURL:destination error:&error];
        if (error != nil) {
            NSLog(@"ForgeTask::MoveFileSchemeStorageToHttpScheme Error migrating LocalStorage: %@", [error localizedDescription]);
        }
    }

    // WebSQL
    NSURL *source = [webSQLDir URLByAppendingPathComponent:sourcePrefix];
    NSURL *destination = [webSQLDir URLByAppendingPathComponent:destinationPrefix];
    if ([source checkResourceIsReachableAndReturnError:&error]) {
        [ForgeMigration moveItemAtURL:source toURL:destination error:&error];
        if (error != nil) {
            NSLog(@"ForgeTask::MoveFileSchemeStorageToHttpScheme Error migrating WebSQL storage: %@", [error localizedDescription]);
        }
    }

    // IndexedDB
    source = [indexedDBDir URLByAppendingPathComponent:sourcePrefix];
    destination = [indexedDBDir URLByAppendingPathComponent:destinationPrefix];
    if ([source checkResourceIsReachableAndReturnError:&error]) {
        [ForgeMigration moveItemAtURL:source toURL:destination error:&error];
        if (error != nil) {
            NSLog(@"ForgeTask::MoveFileSchemeStorageToHttpScheme Error migrating IndexedDB storage: %@", [error localizedDescription]);
        }
    }
}


// - helpers -------------------------------------------------------------------

+ (void)moveItemAtURL:(NSURL*)source toURL:(NSURL*)destination error:(NSError * _Nullable *)error {
    NSFileManager* fm = [NSFileManager defaultManager];
    if ([destination checkResourceIsReachableAndReturnError:nil]) {
        [fm removeItemAtURL:destination error:nil];
    }
    [fm moveItemAtURL:source toURL:destination error:error];
}


+ (void)copyItemAtURL:(NSURL*)source toURL:(NSURL*)destination error:(NSError * _Nullable *)error {
    NSFileManager* fm = [NSFileManager defaultManager];
    if ([destination checkResourceIsReachableAndReturnError:nil]) {
        [fm removeItemAtURL:destination error:nil];
    }
    [fm copyItemAtURL:source toURL:destination error:error];
}


@end
