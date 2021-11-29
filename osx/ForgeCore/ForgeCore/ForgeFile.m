#import "ForgeFile.h"
#import "ForgeLog.h"

/** Object containing information about a file with methods to access it. */
@implementation ForgeFile

/** Constructor with a relative path in the 'src' folder */
- (ForgeFile *)initWithPath:(NSString *)path {
	self = [super init];
	if (self != nil) {
		NSString *newUrl = [[NSBundle mainBundle] pathForResource:@"assets/src" ofType:@""];
		if (![path hasPrefix:@"/"]) {
			newUrl = [newUrl stringByAppendingString:@"/"];
		}

		self->file = @{@"uri" : [newUrl stringByAppendingString:path]};
	}
	return self;
}

/** Constructor with a file object dictionary */
- (ForgeFile *)initWithFile:(NSDictionary *)withFile {
	self = [super init];
	if (self != nil) {
		file = withFile;
	}
	return self;
}

/** Helper constructor that takes either a string or dictionary */
- (ForgeFile*) initWithObject:(NSObject*)object {
	if ([object isKindOfClass:[NSString class]]) {
		return [self initWithPath:(NSString*)object];
	} else {
		return [self initWithFile:(NSDictionary*)object];
	}
}

/** Return a URL that can be used in the WebView to access the resource */
- (NSString*) url {
	return [[[NSURL alloc] initWithScheme:@"file" host:@"" path:[file objectForKey:@"uri"]] absoluteString];
}

/** Whether or not the referenced file exists */
- (void) exists:(ForgeFileExistsResultBlock)resultBlock; {
	resultBlock([[NSFileManager defaultManager] fileExistsAtPath:[file objectForKey:@"uri"]]);
}

/** Access the files data */
- (void) data:(ForgeFileDataResultBlock)resultBlock errorBlock:(ForgeFileErrorBlock)errorBlock {
	resultBlock([NSData dataWithContentsOfFile:[file objectForKey:@"uri"]]);
}

/** Attempt to remove the file */
- (BOOL) remove {
	if ([[file objectForKey:@"uri"] hasPrefix:@"/"]) {
		if ([[NSFileManager defaultManager] removeItemAtPath:[file objectForKey:@"uri"] error:nil]) {
			return YES;
		} else {
			return NO;
		}
	} else {
		return NO;
	}

}

/** Return the files mime-type (if available) */
- (NSString*) mimeType {
	if ([file objectForKey:@"mimeType"] != nil) {
		return [file objectForKey:@"mimeType"];
	} else {
		return @"";
	}
}

/** Return the files dictionary to be converted to JSON */
- (NSDictionary*) toJSON {
	return file;
}

@end
