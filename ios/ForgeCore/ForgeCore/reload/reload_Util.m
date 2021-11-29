#import "NSString+ObjectFromJSONString.h"

#import "reload_Util.h"
#import "ForgeLog.h"
#import "NSFileManager+DoNotBackup.h"
#import "Reachability.h"
#import "ForgeApp.h"
#import "ForgeUtil.h"

static int updateDelay = 1; // ms backoff
static NSThread *updatingThread = nil;
static NSObject *updateLock = @"lock";
static NSString *default_configHash = @"bada5500deadbeaf00c0ffeebabe00133700d00d";

@implementation reload_Util

+ (BOOL)updateAvailable {
    [ForgeLog i:@"Checking for reload update"];
    NSString *snapshotId = @"0";
    NSURL *snapshotPath = [ForgeApp.sharedApp.applicationSupportDirectory URLByAppendingPathComponent:@"live/snapshot"];
    if ([[NSFileManager defaultManager] fileExistsAtPath:[snapshotPath path]]) {
        snapshotId = [[NSString stringWithContentsOfURL:snapshotPath encoding:NSUTF8StringEncoding error:nil] stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
    }

    NSDictionary *appConfig = ForgeApp.sharedApp.appConfig;
    NSString *uuid = [appConfig objectForKey:@"uuid"];
    NSString *triggerDomain = @"https://trigger.io";
    if ([appConfig objectForKey:@"trigger_domain"] != nil) {
        triggerDomain = [appConfig objectForKey:@"trigger_domain"];
    }
    NSString *configHash = [appConfig objectForKey:@"config_hash"];
    if (configHash == nil) {
        configHash = default_configHash;
    }

    [ForgeLog d:[NSString stringWithFormat:@"Checking for reload update with config_hash: %@", configHash]];

    NSUserDefaults *prefs = [NSUserDefaults standardUserDefaults];
    NSString *streamId = @"default";
    if ([prefs objectForKey:@"reload-stream"] != nil) {
        streamId = [prefs objectForKey:@"reload-stream"];
    }
    NSString *installId = @"unknown";
    if ([prefs objectForKey:@"reload-install-id"] != nil) {
        installId = (NSString *)[prefs objectForKey:@"reload-install-id"];
    }
    NSString *versionCode = @"0";
    if ([prefs objectForKey:@"reload-version-code"] != nil) {
        versionCode = (NSString *)[prefs objectForKey:@"reload-version-code"];
    }

    NSString *updateUrl = [NSString stringWithFormat:@"%@/api/reload/%@/updates/latest/%@/%@/%@/%@/%@", triggerDomain, uuid, streamId, configHash, snapshotId, installId, versionCode];
    [ForgeLog d:[NSString stringWithFormat:@"Checking for reload update at URL: %@", updateUrl]];
    NSString *updateResult = [reload_Util stringWithContentsOfURL:[NSURL URLWithString:updateUrl]];
    NSDictionary *updateDict = [updateResult objectFromJSONString];
    if ([[updateDict objectForKey:@"result"] isEqualToString:@"ok"] && ![[updateDict objectForKey:@"latest"] boolValue]) {
        [ForgeLog i:@"reload update available"];
        return YES;
    }
    [ForgeLog i:@"No reload update available."];
    return NO;
}



+ (void)updateWithLock:(ForgeTask*)task {
    @synchronized(updateLock) {
        if (updatingThread != nil && updatingThread != [NSThread currentThread]) {
            NSString *message = @"Reload update already in progress: not proceeding";
            if (task != nil) {
                [task error:message type:@"EXPECTED_FAILURE" subtype:nil];
            }
            [ForgeLog w:message];
            return;
        }
        updatingThread = [NSThread currentThread];
    }
    [ForgeLog i:@"Starting Reload update"];
    [reload_Util update:task];

    @synchronized(updateLock) {
        updatingThread = nil;
    }
}


+ (void)update:(ForgeTask*)task {
    NSURL *applicationSupportDirectory = ForgeApp.sharedApp.applicationSupportDirectory;
    NSURL *updateDir = [applicationSupportDirectory URLByAppendingPathComponent:@"update"];
    [[NSFileManager defaultManager] createDirectoryAtURL:updateDir withIntermediateDirectories:YES attributes:nil error:nil];
    NSURL *liveDir = [applicationSupportDirectory URLByAppendingPathComponent:@"live"];
    [[NSFileManager defaultManager] createDirectoryAtURL:liveDir withIntermediateDirectories:YES attributes:nil error:nil];
    NSURL *updateStatePath = [applicationSupportDirectory URLByAppendingPathComponent:@"update/state"];
    NSURL *updateSnapshotPath = [applicationSupportDirectory URLByAppendingPathComponent:@"update/snapshot"];
    NSURL *manifestPath = [applicationSupportDirectory URLByAppendingPathComponent:@"update/manifest"];

    if ([[NSFileManager defaultManager] fileExistsAtPath:[updateStatePath path]]) {
        NSString *state = [self getUpdateState];
        if ([state hasPrefix:@"complete"]) {
            if (task != nil) {
                [task success:nil];
            }
            [ForgeLog i:@"reload update downloaded and ready to apply"];
            [ForgeApp.sharedApp event:@"reload.updateReady" withParam:[NSNull null]];
            return;
        } else if ([state hasPrefix:@"paused"]) {
            NSString *message = @"Reload updates are paused: call 'update' to resume";
            if (task != nil) {
                [task error:message type:@"EXPECTED_FAILURE" subtype:nil];
            }
            [ForgeLog i:message];
            return;
        }

        if (![[NSFileManager defaultManager] fileExistsAtPath:[manifestPath path]]) {
            // Something has gone wrong, wipe and try again
            [self retryUpdate:task];
            return;
        }
    } else {
        // Clean update, download manifest
        NSUserDefaults *prefs = [NSUserDefaults standardUserDefaults];
        NSString *streamId = @"default";
        if ([prefs objectForKey:@"reload-stream"] != nil) {
            streamId = [prefs objectForKey:@"reload-stream"];
        }
        NSString *snapshotId = @"0";
        NSURL *snapshotPath = [applicationSupportDirectory URLByAppendingPathComponent:@"live/snapshot"];
        if ([[NSFileManager defaultManager] fileExistsAtPath:[snapshotPath path]]) {
            snapshotId = [[NSString stringWithContentsOfURL:snapshotPath encoding:NSUTF8StringEncoding error:nil] stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
        }
        NSDictionary *appConfig = ForgeApp.sharedApp.appConfig;
        NSString *triggerDomain = @"https://trigger.io";
        if ([appConfig objectForKey:@"trigger_domain"] != nil) {
            triggerDomain = [appConfig objectForKey:@"trigger_domain"];
        }
        NSString *configHash = [appConfig objectForKey:@"config_hash"];
        if (configHash == nil) {
            configHash = default_configHash;
        }
        NSString *updateUrl = [NSString stringWithFormat:@"%@/api/reload/%@/updates/%@/%@/%@", triggerDomain, [appConfig objectForKey:@"uuid"], streamId, configHash, snapshotId];
        [ForgeLog d:[NSString stringWithFormat:@"Checking for reload manifest at URL: %@", updateUrl]];
        NSString *updateResult = [reload_Util stringWithContentsOfURL:[NSURL URLWithString:updateUrl]];
        [ForgeLog d:[NSString stringWithFormat:@"Checking for reload manifest got result: %@", updateResult]];
        NSDictionary *updateDict = [updateResult objectFromJSONString];
        if ([[updateDict objectForKey:@"result"] isEqualToString:@"ok"]) {
            NSDictionary *snapshot = [updateDict objectForKey:@"snapshot"];
            if ([snapshot objectForKey:@"manifest_url"] != nil) {
                if (task != nil) {
                    [task success:nil];
                    task = nil;
                }

                NSData *data = [NSData dataWithContentsOfURL:[NSURL URLWithString:[snapshot objectForKey:@"manifest_url"]]];
                if (data == nil) {
                    [ForgeLog w:[NSString stringWithFormat:@"Couldn't download Reload manifest from %@", [snapshot objectForKey:@"manifest_url"]]];
                    return;
                }

                if (![data writeToURL:manifestPath atomically:YES]) {
                    [ForgeLog i:@"Failed to download reload manifest"];
                    return;
                }
                [[NSFileManager defaultManager] addSkipBackupAttributeToItemAtURL:manifestPath];

                [self setUpdateState:@""];
                [[snapshot objectForKey:@"id"] writeToURL:updateSnapshotPath atomically:YES encoding:NSUTF8StringEncoding error:nil];
                [[NSFileManager defaultManager] addSkipBackupAttributeToItemAtURL:updateSnapshotPath];
            } else {
                [ForgeLog i:@"No reload update available."];
                if (task != nil) {
                    [task error:@"No reload update available." type:@"EXPECTED_FAILURE" subtype:nil];
                    task = nil;
                }
                return;
            }
        } else {
            [ForgeLog i:@"Failed to download reload update information."];
            if (task != nil) {
                [task error:@"Failed to download reload update information." type:@"UNEXPECTED_FAILURE" subtype:nil];
                task = nil;
            }
            return;
        }
    }

    if (task != nil) {
        [task success:nil];
        task = nil;
    }

    if ([[NSFileManager defaultManager] fileExistsAtPath:[manifestPath path]]) {
        // Manifest exists, download any files in it we don't yet have
        NSDictionary *manifest = [[[NSString alloc] initWithData:[NSData dataWithContentsOfURL:manifestPath] encoding:NSUTF8StringEncoding] objectFromJSONString];
        NSURL *assetManifestPath = [[NSBundle mainBundle] URLForResource:@"assets/hash_to_file" withExtension:@"json"];
        NSDictionary *assetManifest = [[NSDictionary alloc] init];
        if ([[NSFileManager defaultManager] fileExistsAtPath:[assetManifestPath path]]) {
            assetManifest = [[[NSString alloc] initWithData:[NSData dataWithContentsOfURL:assetManifestPath] encoding:NSUTF8StringEncoding] objectFromJSONString];
        }

        // file -> URL
        NSMutableDictionary *toDownload = [NSMutableDictionary dictionary];

        for (NSString *file in manifest) {
            NSString *url = [manifest objectForKey:file];
            NSURL *parsedURL = [NSURL URLWithString:url];
            if (parsedURL == nil) {
                [ForgeLog i:[NSString stringWithFormat:@"Malformed URL: %@", url]];
                [self retryUpdate:task];
                return;
            }
            NSString *hash = [parsedURL lastPathComponent];

            if (![[NSFileManager defaultManager] fileExistsAtPath:[[liveDir URLByAppendingPathComponent:hash] path]] &&
                ![[NSFileManager defaultManager] fileExistsAtPath:[[updateDir URLByAppendingPathComponent:hash] path]]) {
                if ([assetManifest objectForKey:hash] != nil) {
                    NSError *error = nil;
                    NSURL *filePath = [[NSBundle mainBundle] URLForResource:[NSString stringWithFormat:@"assets/src/%@",[assetManifest objectForKey:hash]] withExtension:@""];
                    NSURL *linkPath = [updateDir URLByAppendingPathComponent:hash];

                    [ForgeLog d:[NSString stringWithFormat:@"copying existing asset file from %@ to %@", filePath, linkPath]];
                    [[NSFileManager defaultManager] copyItemAtURL:filePath toURL:linkPath error:&error];
                    if (error != nil) {
                        [ForgeLog e:error];
                    }
                } else {
                    toDownload[file] = url;
                }
            }
        }

        [ForgeLog i:[NSString stringWithFormat:@"We have %lu Reload files to download", (unsigned long)[toDownload count]]];
        NSMutableDictionary *progress = [NSMutableDictionary dictionary];
        progress[@"total"] = [NSNumber numberWithInteger:[toDownload count]];
        progress[@"completed"] = [NSNumber numberWithInt:0];
        for (NSString *file in toDownload) {
            if ([@"paused" isEqualToString:[self getUpdateState]]) {
                [ForgeLog i:@"Pausing Reload update: call 'update' to resume..."];
                return;
            }
            NSString *url = [manifest objectForKey:file];
            NSURL *parsedURL = [NSURL URLWithString:url];
            if (parsedURL == nil) {
                [ForgeLog i:[NSString stringWithFormat:@"Malformed URL: %@", url]];
                [self retryUpdate:task];
                return;
            }
            NSString *hash = [parsedURL lastPathComponent];

            // Attempt to download content file, retrying up to 10 times before giving up
            NSData *data = nil;
            NSError *error = nil;
            for (int retryCount = 0; retryCount < 10; retryCount++) {
                [ForgeLog d:[NSString stringWithFormat:@"Downloading reload file: %@ (%@)", file, hash]];
                error = nil;
                data = [NSData dataWithContentsOfURL:[NSURL URLWithString:url] options:NSDataReadingUncached error:&error];
                if (error) {
                    [ForgeLog i:[NSString stringWithFormat:@"Failed to download reload update file: %@\n%@", url, [error localizedDescription]]];
                    [ForgeLog i:[NSString stringWithFormat:@"Trying again: %d/10", retryCount]];
                    [ForgeLog d:[NSString stringWithFormat:@"Backing off download retry for %dms", [self getUpdateDelay]]];
                    [NSThread sleepForTimeInterval:[self getUpdateDelay] / 1000];
                    [ForgeLog d:@"waking up"];
                    [self increaseUpdateDelay];
                } else {
                    break;
                }
            }
            if (error) {
                [ForgeLog i:[NSString stringWithFormat:@"Failed to download reload update file. Giving up: %@\n%@", url, [error localizedDescription]]];
                [self retryUpdate:task];
                return;
            }

            if ([data writeToURL:[updateDir URLByAppendingPathComponent:hash] atomically:YES]) {
                [[NSFileManager defaultManager] addSkipBackupAttributeToItemAtURL:[updateDir URLByAppendingPathComponent:hash]];
                [ForgeLog d:[NSString stringWithFormat:@"Downloaded reload file: %@ (%@)", file, hash]];
                NSNumber *oldCompleted = progress[@"completed"];
                progress[@"completed"] = [NSNumber numberWithInt:([oldCompleted intValue] + 1)];
                [ForgeApp.sharedApp event:@"reload.updateProgress" withParam:progress];
            } else {
                // clean and start again in case of broken manifest
                [ForgeLog i:@"Failed to download reload update file"];
                [self retryUpdate:task];
                return;
            }
        }
        // All files downloaded
        [self setUpdateState:@"completed"];
        [ForgeLog i:@"reload update downloaded and ready to apply"];
        [ForgeApp.sharedApp event:@"reload.updateReady" withParam:[NSNull null]];
    } else {
        [ForgeLog w:@"Unexpected error attempting to download reload update: manifest not found"];
        [self retryUpdate:task];
    }
}

+ (void)applyUpdate:(ForgeTask*)task {
    NSLog(@"Applying update");
    NSURL *applicationSupportDirectory = ForgeApp.sharedApp.applicationSupportDirectory;
    NSURL *updateDir = [applicationSupportDirectory URLByAppendingPathComponent:@"update"];
    NSURL *updatePath = [applicationSupportDirectory URLByAppendingPathComponent:@"update/state"];
    if ([[NSFileManager defaultManager] fileExistsAtPath:[updatePath path]]) {
        NSString *state = [[NSString alloc] initWithData:[NSData dataWithContentsOfURL:updatePath] encoding:NSUTF8StringEncoding];
        if (![state hasPrefix:@"complete"]) {
            if (task != nil) {
                [task error:@"No completed update available to apply." type:@"EXPECTED_FAILURE" subtype:nil];
            }
            [ForgeLog i:@"No completed update available to apply."];
            return;
        }
    } else {
        if (task != nil) {
            [task error:@"No completed update available to apply." type:@"EXPECTED_FAILURE" subtype:nil];
        }
        [ForgeLog i:@"No completed update available to apply."];
        return;
    }
    NSURL *manifestPath = [applicationSupportDirectory URLByAppendingPathComponent:@"update/manifest"];
    NSDictionary *manifest;
    if ([[NSFileManager defaultManager] fileExistsAtPath:[manifestPath path]]) {
        manifest = [[[NSString alloc] initWithData:[NSData dataWithContentsOfURL:manifestPath] encoding:NSUTF8StringEncoding] objectFromJSONString];
    } else {
        if (task != nil) {
            [task error:@"Unexpected error attempting to apply reload update." type:@"UNEXPECTED_FAILURE" subtype:nil];
        }
        [ForgeLog i:@"Unexpected error attempting to apply reload update"];
        [self retryUpdate:task];
        return;
    }

    // grab actual hash off end of download URL
    NSArray *hashURLs = [manifest allValues];
    NSMutableArray *hashes = [NSMutableArray arrayWithCapacity:[hashURLs count]];
    [hashURLs enumerateObjectsUsingBlock:^(id obj, NSUInteger idx, BOOL *stop) {
        NSURL *url = [NSURL URLWithString:[hashURLs objectAtIndex:idx]];
        if (url == nil) {
            [ForgeLog i:[NSString stringWithFormat:@"Malformed URL: %@", [hashURLs objectAtIndex:idx]]];
            [self retryUpdate:task];
            return;
        }
        [hashes addObject:[url lastPathComponent]];
    }];

    NSURL *livePath = [applicationSupportDirectory URLByAppendingPathComponent:@"live"];
    NSArray *files = [[NSFileManager defaultManager] contentsOfDirectoryAtURL:livePath includingPropertiesForKeys:[NSArray arrayWithObject:NSURLNameKey] options:NSDirectoryEnumerationSkipsHiddenFiles error:nil];
    for (NSURL *file in files) {
        if ([hashes indexOfObject:[file lastPathComponent]] == NSNotFound) {
            [ForgeLog d:[NSString stringWithFormat:@"Reload: removing %@ from live", file]];
            [[NSFileManager defaultManager] removeItemAtURL:file error:nil];
        }
    }

    files = [[NSFileManager defaultManager] contentsOfDirectoryAtURL:updateDir includingPropertiesForKeys:[NSArray arrayWithObject:NSURLNameKey] options:NSDirectoryEnumerationSkipsHiddenFiles error:nil];
    for (NSURL *file in files) {
        [ForgeLog d:[NSString stringWithFormat:@"Reload: moving %@ from update to live", file]];
        [[NSFileManager defaultManager] moveItemAtURL:file toURL:[livePath URLByAppendingPathComponent:[file lastPathComponent]] error:nil];
    }

    NSUserDefaults *prefs = [NSUserDefaults standardUserDefaults];
    // Remove existing assets folder
    [[NSFileManager defaultManager] removeItemAtURL:[ForgeApp.sharedApp assetsFolderLocationWithPrefs:prefs] error:nil];

    // Create new UUID for assets location to workaround iOS 6 caching.
    NSString *uuid = (__bridge_transfer NSString *)CFUUIDCreateString(kCFAllocatorDefault, CFUUIDCreate(kCFAllocatorDefault));
    [prefs setValue:uuid forKey:@"reload-assets-id"];
    [prefs synchronize];

    // Create new assets folder and symlink forge
    NSURL *assetsFolder = [ForgeApp.sharedApp assetsFolderLocationWithPrefs:prefs];
    NSURL *bundleFromAssets = ForgeApp.sharedApp.bundleLocationRelativeToAssets;
    [[NSFileManager defaultManager] createDirectoryAtURL:assetsFolder
                              withIntermediateDirectories:YES
                                               attributes:nil
                                                    error:nil];
    [[NSFileManager defaultManager] createSymbolicLinkAtURL:[assetsFolder URLByAppendingPathComponent:@"forge"]
                                         withDestinationURL:[bundleFromAssets URLByAppendingPathComponent:@"assets/forge"]
                                                       error:nil];
    [[NSFileManager defaultManager] addSkipBackupAttributeToItemAtURL:[assetsFolder URLByAppendingPathComponent:@"forge"]];

    // Create new src folder
    [[NSFileManager defaultManager] createDirectoryAtURL:[assetsFolder URLByAppendingPathComponent:@"src"]
                              withIntermediateDirectories:YES
                                               attributes:nil
                                                    error:nil];

    // Create hard links for all files in manifest
    [manifest enumerateKeysAndObjectsUsingBlock:^(id key, id obj, BOOL *stop) {
        if ([key rangeOfString:@"/"].location != NSNotFound) {
            // Make sure directory exists
            [[NSFileManager defaultManager]
             createDirectoryAtURL:[[assetsFolder URLByAppendingPathComponent:@"src"]
                                    URLByAppendingPathComponent:[key substringToIndex:[key rangeOfString:@"/" options:NSBackwardsSearch].location]]
             withIntermediateDirectories:YES
             attributes:nil
             error:nil];
        }
        // Hard link file
        NSArray *chunks = [obj componentsSeparatedByString: @"/"];
        NSURL *linkPath = [[assetsFolder URLByAppendingPathComponent:@"src"] URLByAppendingPathComponent:key];
        NSURL *filePath = [livePath URLByAppendingPathComponent:[chunks objectAtIndex:([chunks count] - 1)]];

        NSError *error;
        [ForgeLog d:[NSString stringWithFormat:@"creating hard link at %@ to %@", linkPath, filePath]];
        [[NSFileManager defaultManager] linkItemAtURL:filePath toURL:linkPath error:&error];
        if (error != nil) {
            [ForgeLog e:error];
        }
        [[NSFileManager defaultManager] addSkipBackupAttributeToItemAtURL:linkPath];
    }];

    [ForgeLog i:@"reload update applied successfully."];
    if (task != nil) {
        [task success:nil];
    }
}

+(NSString*)getUpdateState {
    NSURL *applicationSupportDirectory = ForgeApp.sharedApp.applicationSupportDirectory;
    NSURL *updateStatePath = [applicationSupportDirectory URLByAppendingPathComponent:@"update/state"];
    if ([[NSFileManager defaultManager] fileExistsAtPath:[updateStatePath path]]) {
        NSString *state = [[NSString alloc] initWithData:[NSData dataWithContentsOfURL:updateStatePath] encoding:NSUTF8StringEncoding];
        return state;
    } else {
        return nil;
    }
}

+(void)setUpdateState:(NSString *)updateState {
    NSURL *applicationSupportDirectory = ForgeApp.sharedApp.applicationSupportDirectory;
    NSURL *updateStatePath = [applicationSupportDirectory URLByAppendingPathComponent:@"update/state"];
    NSError *error;
    [updateState writeToURL:updateStatePath atomically:YES encoding:NSUTF8StringEncoding error:&error];
    if (error != nil) {
        [ForgeLog e:error];
    }
    [[NSFileManager defaultManager] addSkipBackupAttributeToItemAtURL:updateStatePath];
}

+(int)getUpdateDelay {
    return updateDelay;
}
+(void)increaseUpdateDelay {
    if ((updateDelay * 2) < 1000 * 60 * 60) {
        updateDelay *= 2;
    }
}
+(void)retryUpdate:(ForgeTask *)task {
    NSURL *applicationSupportDirectory = ForgeApp.sharedApp.applicationSupportDirectory;
    NSURL *updateDir = [applicationSupportDirectory URLByAppendingPathComponent:@"update"];

    [ForgeLog d:[NSString stringWithFormat:@"Backing off Reload retry for %dms", [self getUpdateDelay]]];
    [NSThread sleepForTimeInterval:[self getUpdateDelay] / 1000];
    [ForgeLog d:@"waking up"];
    [self increaseUpdateDelay];

    [[NSFileManager defaultManager] removeItemAtURL:updateDir error:nil];
    [self updateWithLock:task];
}

+ (BOOL)reloadManual {
    NSDictionary *config = [[ForgeApp.sharedApp.appConfig objectForKey:@"core"] objectForKey:@"general"];
    if (![[config objectForKey:@"reload"] boolValue]) {
        return false;
    }
    bool manual = false;
    if ([config objectForKey:@"reload_manual"] != nil) {
        manual = [[config objectForKey:@"reload_manual"] boolValue];
    }
    if (manual) {
        [ForgeLog d:@"Reload's automated functionality has been disabled."];
    }
    return manual;
}

+ (BOOL)reloadEnabled {
    NSDictionary *config = [[ForgeApp.sharedApp.appConfig objectForKey:@"core"] objectForKey:@"general"];
    if (![[config objectForKey:@"reload"] boolValue]) {
        return false;
    }
    bool forcewifi = false;
    if ([config objectForKey:@"reload_forcewifi"] != nil) {
        forcewifi = [[config objectForKey:@"reload_forcewifi"] boolValue];
    }

    TMReachability *reachability = [TMReachability reachabilityForInternetConnection];
    [reachability startNotifier];

    NetworkStatus status = [reachability currentReachabilityStatus];
    if (status == NotReachable) {
        [ForgeLog d:@"Reload has no network connectivity"];
        return false;
    } else if (status == ReachableViaWiFi) {
        [ForgeLog d:@"Reload has WiFi network connectivity"];
        return true;
    } else if (status == ReachableViaWWAN) {
        [ForgeLog d:[NSString stringWithFormat:@"Reload has Mobile network connectivity: %d", forcewifi]];
        return (forcewifi == false);
    } else {
        [ForgeLog d:@"Reload has unknown network connectivity"];
    }

    return true;
}

+ (NSString*) stringWithContentsOfURL:(NSURL*)url {
    NSURLRequest* request = [NSURLRequest requestWithURL:url cachePolicy:NSURLRequestReloadIgnoringLocalAndRemoteCacheData timeoutInterval:5];
    NSURLResponse* response = nil;
    NSError* error = nil;
    NSData* data = [ForgeUtil sendSynchronousRequest:request returningResponse:&response error:&error];
    if (error == nil && data != nil) {
        return [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding];
    } else {
        NSLog(@"reload_Util::stringWithContentsOfURL Error: %@", error);
        return [NSString stringWithFormat:@"{\"text\": \"%@\", \"result\": \"error\"}", [error localizedDescription]];
    }
}


@end
