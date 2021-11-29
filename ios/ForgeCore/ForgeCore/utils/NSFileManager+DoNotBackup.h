@interface NSFileManager (DoNotBackup)

- (BOOL)addSkipBackupAttributeToItemAtURL:(NSURL *)URL;
- (BOOL)addSkipBackupAttributeToItemAtPath:(NSString *)path;

@end