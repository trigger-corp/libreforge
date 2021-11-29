#import "inspector_API.h"
#import "ForgeTask.h"
#import "ForgeApp.h"

@implementation inspector_API

+ (void)list:(ForgeTask*)task {
	[task success:[[ForgeApp sharedApp] getAPIMethodInfo]];
}

@end
