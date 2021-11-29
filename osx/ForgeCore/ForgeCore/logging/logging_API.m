#import "logging_API.h"
#import "ForgeTask.h"
#import "ForgeLog.h"

@implementation logging_API

+ (void)log:(ForgeTask*)task message:(NSString *)message level:(NSNumber *)level {
	switch ([level intValue]) {
		case 10:
			[ForgeLog d:message];
			break;
		case 20:
			[ForgeLog i:message];
			break;
		case 30:
			[ForgeLog w:message];
			break;
		case 40:
			[ForgeLog e:message];
			break;
		case 50:
			[ForgeLog c:message];
			break;
		default:
			[ForgeLog i:message];
			break;
	}
	[task success:nil];
}

@end
