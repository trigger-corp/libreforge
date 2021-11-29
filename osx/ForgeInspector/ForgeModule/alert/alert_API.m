#import "alert_API.h"

@implementation alert_API

+ (void)show:(ForgeTask*)task text:(NSString *)text {
	if ([text length] == 0) {
		[task error:@"You must enter a message"];
		return;
	}
	NSAlert *alert = [[NSAlert alloc] init];
    [alert addButtonWithTitle:@"OK"];
    [alert setMessageText:text];
    [alert runModal];
	[task success:nil];
}


@end
