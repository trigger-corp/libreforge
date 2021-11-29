#import "inspector_API.h"


@implementation inspector_API

+ (void)list:(ForgeTask*)task {
	[task success:[BorderControl getAPIMethodInfo]];
}

@end
