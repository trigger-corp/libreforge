#import "tools_API.h"

@implementation tools_API

+ (void)getURL:(ForgeTask*)task name:(NSString*)url {
	if ([url hasPrefix:@"http://"] || [url hasPrefix:@"https://"]) {
		[task success:url];
	} else {
		if (![url hasPrefix:@"/"]) {
			url = [@"/" stringByAppendingString:url];
		}
		NSString *path = [[NSBundle mainBundle] pathForResource:[NSString stringWithFormat:@"assets/src%@", url] ofType:@""];
		if (path != nil) {
			[task success:[[[NSURL alloc] initWithScheme:@"file" host:@"" path:path] absoluteString]];
		} else {
			[task error:@"Not a valid path" type:@"EXPECTED_FAILURE" subtype:nil];
		}
	}
}

@end
