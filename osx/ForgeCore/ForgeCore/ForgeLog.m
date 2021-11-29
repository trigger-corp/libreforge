#import "ForgeLog.h"

/**
 * Used to output log entries to the console / Trigger toolkit.
 */
@implementation ForgeLog

NSString* const kForgeLogLevel = @"DEBUG";

/**
 * Log a debug level message
 * @param msg Object to output.
 */
+ (void) d:(id)msg {
	if (![kForgeLogLevel isEqualToString:@"INFO"] &&
			![kForgeLogLevel isEqualToString:@"WARNING"] &&
			![kForgeLogLevel isEqualToString:@"ERROR"] &&
			![kForgeLogLevel isEqualToString:@"CRITICAL"]) {
		NSLog(@"[DEBUG] %@", msg);
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
		NSLog(@"[INFO] %@", msg);
	}
}

/**
 * Log a warning level message
 * @param msg Object to output.
 */
+ (void) w:(id)msg {
	if (![kForgeLogLevel isEqualToString:@"ERROR"] &&
		![kForgeLogLevel isEqualToString:@"CRITICAL"]) {
			NSLog(@"[WARNING] %@", msg);
	}
}


/**
 * Log an error level message
 * @param msg Object to output.
 */
+ (void) e:(id)msg {
	if (![kForgeLogLevel isEqualToString:@"CRITICAL"]) {
		NSLog(@"[ERROR] %@", msg);
	}
}

/**
 * Log a critical level message
 * @param msg Object to output.
 */
+ (void) c:(id)msg {
	NSLog(@"[CRITICAL] %@", msg);
}

@end
