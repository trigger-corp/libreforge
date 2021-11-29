#import "NSFileManager+DoNotBackup.h"
#include <sys/xattr.h>

@implementation NSFileManager (DoNotBackup)

- (BOOL)addSkipBackupAttributeToItemAtURL:(NSURL *)URL
{
	if (![[NSFileManager defaultManager] fileExistsAtPath: [URL path]]) {
		NSLog(@"Error excluding %@ from backup. File does not exist", URL);
	}
	
	BOOL isURLIsExcludedFromBackupKeyAvailable = (&NSURLIsExcludedFromBackupKey) != nil;
	if (!isURLIsExcludedFromBackupKeyAvailable) { // iOS <= 5.0.1
		const char* filePath = [[URL path] fileSystemRepresentation];
		const char* attrName = "com.apple.MobileBackup";
		u_int8_t attrValue = 1;
		int result = setxattr(filePath, attrName, &attrValue, sizeof(attrValue), 0, 0);
		if (result != 0) {
			NSLog(@"Error excluding %@ from backup", [URL lastPathComponent]);
		}
		return result == 0;
		
	} else { // iOS >= 5.1
		NSError *error = nil;
		BOOL success = [URL setResourceValue:[NSNumber numberWithBool:YES] forKey:@"NSURLIsExcludedFromBackupKey" error:&error];
		if (!success) {
			NSLog(@"Error excluding %@ from backup %@", [URL lastPathComponent], error);
		}
		return success;
	}
}

- (BOOL)addSkipBackupAttributeToItemAtPath:(NSString *)path {
    return [self addSkipBackupAttributeToItemAtURL:[NSURL fileURLWithPath:path]];
}

@end
