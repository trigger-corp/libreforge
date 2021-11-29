#include <pthread.h>
#include <os/log.h>

#import "ForgeLog.h"

/**
 * Used to output log entries to the console / Trigger toolkit.
 */
@implementation ForgeLog

static NSString* kForgeLogLevel = @"DEBUG";
static os_log_t simulator_log;
static BOOL _isSimulator;


/**
 * Initialize logging subsystems
 */
+ (void)start {
#if TARGET_OS_SIMULATOR
    _isSimulator = YES;
    NSString *bundleIdentifier = [[NSBundle mainBundle] bundleIdentifier];
    simulator_log = os_log_create(bundleIdentifier.UTF8String, "Forge");
#else
    _isSimulator = NO;
#endif
}


/**
 * Whether we are running on the simulator or not
 */
+ (BOOL)isSimulator {
    return _isSimulator;
}


/**
 * Set the log level
 */
+ (void)setLogLevel:(NSString *)level {
    if ([level isEqualToString:@"DEBUG"] || [level isEqualToString:@"INFO"] || [level isEqualToString:@"WARNING"] || [level isEqualToString:@"ERROR"] || [level isEqualToString:@"CRITICAL"]) {
        kForgeLogLevel = [level copy];
    }
}

/**
 * Log a debug level message
 * @param msg Object to output.
 */
+ (void) d:(id)msg {
    if (![kForgeLogLevel isEqualToString:@"INFO"] &&
            ![kForgeLogLevel isEqualToString:@"WARNING"] &&
            ![kForgeLogLevel isEqualToString:@"ERROR"] &&
            ![kForgeLogLevel isEqualToString:@"CRITICAL"]) {
        TFLog(@"[DEBUG] %@", msg);
    }
}

/**
 * Log an info level message
 * @param msg Object to output.
 */
+ (void) i:(id)msg {
    if (![kForgeLogLevel isEqualToString:@"WARNING"] &&
        ![kForgeLogLevel isEqualToString:@"ERROR"] &&
        ![kForgeLogLevel isEqualToString:@"CRITICAL"]) {
        TFLog(@"[INFO] %@", msg);
    }
}

/**
 * Log a warning level message
 * @param msg Object to output.
 */
+ (void) w:(id)msg {
    if (![kForgeLogLevel isEqualToString:@"ERROR"] &&
        ![kForgeLogLevel isEqualToString:@"CRITICAL"]) {
        TFLog(@"[WARNING] %@", msg);
    }
}


/**
 * Log an error level message
 * @param msg Object to output.
 */
+ (void) e:(id)msg {
    if (![kForgeLogLevel isEqualToString:@"CRITICAL"]) {
        TFLog(@"[ERROR] %@", msg);
    }
}

/**
 * Log a critical level message
 * @param msg Object to output.
 */
+ (void) c:(id)msg {
    TFLog(@"[CRITICAL] %@", msg);
}


/**
 * NSLog replacement which behaves in a manner one would expect of logging function
 */
void TFLog(NSString *format, ...) {
    static NSDateFormatter *timeStampFormat;
    if (!timeStampFormat) {
        timeStampFormat = [[NSDateFormatter alloc] init];
        [timeStampFormat setDateFormat:@"yyyy-MM-dd HH:mm:ss.SSSSSSZZZ"];
        [timeStampFormat setTimeZone:[NSTimeZone systemTimeZone]];
    }

    NSString *msg;
    va_list args;
    va_start(args, format);
        msg = [[NSString alloc] initWithFormat:format arguments:args];
    va_end(args);

    // Log to system logging subsystem
    os_log(simulator_log, "%s", [msg UTF8String]);

    // Log to stdout when using hardware so we can still get log output when apps are being run inside lldb.
    if (!ForgeLog.isSimulator) {
        __uint64_t threadId;
        if (pthread_threadid_np(0, &threadId)) {
            threadId = pthread_mach_thread_np(pthread_self());
        }
        NSString *prefix = [NSString stringWithFormat:@"%@ %@[%d:%ld]",
                            [timeStampFormat stringFromDate:[NSDate date]],
                            [[NSProcessInfo processInfo] processName],
                            [[NSProcessInfo processInfo] processIdentifier],
                            (long) threadId];
        fprintf(stdout, "%s %s\n", [prefix UTF8String], [msg UTF8String]);
    }
}

@end
