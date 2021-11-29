#import "ForgeStorage.h"


typedef void (^ForgeFileResultBlock)(void);
typedef void (^ForgeFileExistsResultBlock)(BOOL exists);
typedef void (^ForgeFileInfoResultBlock)(NSDictionary* info);
typedef void (^ForgeFileContentsResultBlock)(NSData* data);
typedef void (^ForgeFileErrorBlock)(NSError* error);
typedef void (^ForgeFileErrorDescriptionBlock)(NSString* description);


@interface ForgeFile : NSObject

@property (readonly) EndpointId* endpointId;
@property (readonly) NSString*   endpoint;
@property (readonly) NSString*   resource;
@property (readonly) NSString*   mimeType;

+ (ForgeFile*)withEndpointId:(EndpointId*)endpointId resource:(NSString*)resource;
+ (ForgeFile*)withScriptObject:(NSDictionary*)scriptObject error:(NSError**)error;

- (NSDictionary*) toScriptObject;

- (void) exists:(ForgeFileExistsResultBlock)resultBlock;
- (void) attributes:(ForgeFileInfoResultBlock)resultBlock errorBlock:(ForgeFileErrorDescriptionBlock)errorBlock;
- (void) contents:(ForgeFileContentsResultBlock)resultBlock errorBlock:(ForgeFileErrorBlock)errorBlock;
- (void) remove:(ForgeFileResultBlock)resultBlock errorBlock:(ForgeFileErrorBlock)errorBlock;

@end
