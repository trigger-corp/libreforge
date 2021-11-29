#import "ForgeApp.h"
#import "ForgeEventListener.h"
#import "ForgeLog.h"
#import "BorderControl.h"
#import "ForgeMigration.h"
#import "NSFileManager+DirectoryLocations.h"
#import "NSString+ObjectFromJSONString.h"


#import <objc/objc.h>
#import <objc/runtime.h>

typedef void (^EventListenerBlock_t)(Class class, NSUInteger idx, BOOL *stop);

static ForgeApp *sharedSingleton;

/** ForgeApp is a singleton that allows global access to various useful objects and methods */
@implementation ForgeApp

@synthesize webView, appConfig, moduleMapping, appDelegate, viewController, inspectorEnabled;


#pragma mark life-cycle

+ (void)initialize {
    static BOOL initialized = NO;
    if (!initialized) {
        initialized = YES;
        sharedSingleton = [[ForgeApp alloc] init];
        sharedSingleton.appConfig = [[[NSString alloc] initWithData:[[NSFileManager defaultManager] contentsAtPath:[[NSBundle mainBundle] pathForResource:@"assets/app_config.json" ofType:@""]] encoding:NSUTF8StringEncoding] objectFromJSONString];
        sharedSingleton.moduleMapping = [[[NSString alloc] initWithData:[[NSFileManager defaultManager] contentsAtPath:[[NSBundle mainBundle] pathForResource:@"assets/module_mapping.json" ofType:@""]] encoding:NSUTF8StringEncoding] objectFromJSONString];
        sharedSingleton.eventListeners = [[NSMutableArray alloc] init];
        sharedSingleton.inspectorEnabled = NO;

        // migrate web storage
        if ([ForgeApp.sharedApp flag:@"migrate_web_storage_for_webview"] == YES) {
            [ForgeMigration MoveOldWebViewStorageToWKWebView];
        }
        if ([ForgeApp.sharedApp flag:@"move_filescheme_storage_to_httpscheme"] == YES) {
            [ForgeMigration MoveFileSchemeStorageToHttpScheme];
        }

        // Set logging level and start logging
        NSString *level = [[[[sharedSingleton.appConfig objectForKey:@"core"] objectForKey:@"general"] objectForKey:@"logging"] objectForKey:@"level"];
        [ForgeLog setLogLevel:level];
        [ForgeLog start];
    }
}

- (id)init
{
    self = [super init];
    if (self) {
    }
    return self;
}


#pragma mark interface

/**
 * Access shared singleton
 */
+ (ForgeApp*)sharedApp {
    return sharedSingleton;
}

- (id)nativeEvent:(SEL)selector withArgs:(NSArray*)args {
    if (inspectorEnabled) {
        [ForgeApp.sharedApp event:@"inspector.eventTriggered" withParam:@{
            @"name": NSStringFromSelector(selector)
        }];
    }

    Method superMethod = class_getClassMethod([ForgeEventListener class], selector);

    __block id returnValue = nil;

    EventListenerBlock_t enumerator = ^(Class class, NSUInteger idx, BOOL *stop) {
        Method method = class_getClassMethod(class, selector);
        // Only call methods that are overriden (except in the special case later in this method)
        if (method != superMethod || idx == 99999) {
            NSMethodSignature *sig = [class methodSignatureForSelector:selector];

            if (idx == 99999 && strcmp([sig methodReturnType],@encode(void)) == 0) {
                // Don't call the default version if we don't need a return value
                return;
            }

            NSInvocation *inv = [NSInvocation invocationWithMethodSignature:sig];
            [inv setTarget:class];
            [inv setSelector:selector];

            for (int i = 0; i < [args count]; i++) {
                id arg = [args objectAtIndex:i];

                const char * type = [sig getArgumentTypeAtIndex:i+2];
                if ([arg isEqual:[NSNull null]]) {
                    arg = nil;
                    [inv setArgument:&arg atIndex:i+2];
                } else if (strcmp(type, @encode(id)) == 0) {
                    [inv setArgument:&arg atIndex:i+2];

                } else if (strcmp(type, @encode(bool)) == 0) {
                    bool value = ((NSNumber*)arg).boolValue;
                    [inv setArgument:&value atIndex:i+2];

                } else if (strcmp(type, @encode(int)) == 0) {
                    int value = ((NSNumber*)arg).intValue;
                    [inv setArgument:&value atIndex:i+2];

                } else if (strcmp(type, @encode(long long)) == 0) {
                    long long value = ((NSNumber*)arg).longLongValue;
                    [inv setArgument:&value atIndex:i+2];

                }  else if (strcmp(type, @encode(double)) == 0) {
                    double value = ((NSNumber*)arg).doubleValue;
                    [inv setArgument:&value atIndex:i+2];
                } else if (strcmp(type, @encode(CGPoint)) == 0) {
                    CGPoint value = [((NSValue*)arg) CGPointValue];
                    [inv setArgument:&value atIndex:i+2];
                } else if (strcmp(type, @encode(CGSize)) == 0) {
                    CGSize value = [((NSValue*)arg) CGSizeValue];
                    [inv setArgument:&value atIndex:i+2];
                } else if (strcmp(type, @encode(CGRect)) == 0) {
                    CGRect value = [((NSValue*)arg) CGRectValue];
                    [inv setArgument:&value atIndex:i+2];
                } else {
                    [ForgeLog e:[NSString stringWithFormat:@"Unhandled event listener argument type: %@:%@ -> %d:%s", NSStringFromClass(class), NSStringFromSelector(selector), i, type]];
                }
            }

            if (self->inspectorEnabled) {
                [ForgeApp.sharedApp event:@"inspector.eventInvoked" withParam:@{
                    @"name": NSStringFromSelector(selector),
                    @"class": NSStringFromClass(class)
                }];
            }

            [inv invoke];

            if (strcmp([[inv methodSignature] methodReturnType],@encode(void)) == 0) {
                // Returned void, continue
                return;
            }

            [inv getReturnValue:&returnValue];
            // Transfer ownership to ARC
            CFBridgingRetain(returnValue);

            if (returnValue == nil) {
                // Returned nil, continue
                return;
            }

            // If we got this far we have a return value, prevent any further listeners from running
            *stop = YES;
        }
    };

    [[self eventListeners] enumerateObjectsUsingBlock:enumerator];

    if (returnValue == nil) {
        // If we have no returnValue try to get a default
        BOOL stop;
        enumerator([ForgeEventListener class], 99999, &stop);
    }

    return returnValue;
}


/**
 * Trigger an event in JavaScript
 *
 * @param name the event name the JavaScript should set a listener for
 * @param params *(optional)* the object that will be passed to the JavaScript event listener
 */
 - (void)event:(NSString *)name withParam:(id)params {
    if (params == nil) {
        params = [NSNull null];
    }
    NSDictionary *returnObj = @{@"params" : params, @"event" : name};

    // Send the event back to the webview from the main thread
    if ([NSThread isMainThread]) {
        [BorderControl returnResult:returnObj toWebView:webView];
    } else {
        dispatch_async(dispatch_get_main_queue(), ^{
            [BorderControl returnResult:returnObj toWebView:self->webView];
        });
    }
}

/**
 * Helper to access config for a particular plugin.
 */
- (NSDictionary*)configForModule:(NSString*)name {
    return [[[[self appConfig] objectForKey:@"modules"] objectForKey:[moduleMapping objectForKey:name]] objectForKey:@"config"];
}

- (NSDictionary*)configForPlugin:(NSString*)name {
    return [self configForModule:name];
}

- (NSURL*)bundleLocationRelativeToAssets {
    return [[NSBundle mainBundle] bundleURL];
}


#pragma mark assets directory - TODO this should be private to ForgeCore

- (NSURL*)applicationSupportDirectory {
    NSString *executableName = [[[NSBundle mainBundle] infoDictionary] objectForKey:@"CFBundleExecutable"];
    NSError *error;
    NSString *path = [NSFileManager.defaultManager findOrCreateDirectory:NSApplicationSupportDirectory
                                                                inDomain:NSUserDomainMask
                                                     appendPathComponent:executableName
                                                                   error:&error];
    if (error != nil) {
        NSLog(@"Unable to find or create application support directory:\n%@", error);
        return nil;
    }

    return [NSURL fileURLWithPath:path isDirectory:YES];
}

- (NSURL*)assetsFolderLocationWithPrefs:(NSUserDefaults*)prefs {
    NSURL* applicationSupportDirectory = [self applicationSupportDirectory];
    return [applicationSupportDirectory URLByAppendingPathComponent:[NSString stringWithFormat:@"assets-%@", [prefs objectForKey:@"reload-assets-id"]]];;
}


#pragma mark feature flag support

- (BOOL)flag:(NSString*)name {
    NSNumber *flag = [[ForgeApp.sharedApp.appConfig objectForKey:@"flags"] objectForKey:name];
    if (flag != nil) {
        return [flag boolValue];
    }
    return NO;
}

@end
