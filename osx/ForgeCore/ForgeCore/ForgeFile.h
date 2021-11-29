#import <Foundation/Foundation.h>

typedef void (^ForgeFileExistsResultBlock)(BOOL exists);
typedef void (^ForgeFileDataResultBlock)(NSData* data);
typedef void (^ForgeFileErrorBlock)(NSError* error);

@interface ForgeFile : NSObject {
	NSDictionary* file;
}

- (ForgeFile*) initWithPath:(NSString*)path;
- (ForgeFile*) initWithFile:(NSDictionary*)withFile;
- (ForgeFile*) initWithObject:(NSObject*)object;
- (NSString*) url;
- (void) exists:(ForgeFileExistsResultBlock)resultBlock;
- (void) data:(ForgeFileDataResultBlock)resultBlock errorBlock:(ForgeFileErrorBlock)errorBlock;
- (BOOL) remove;
- (NSString*) mimeType;
- (NSDictionary*) toJSON;

@end
