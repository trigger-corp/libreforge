#import <Foundation/Foundation.h>


NS_ASSUME_NONNULL_BEGIN

#pragma mark Forward Declarations

@class ForgeFile;


#pragma mark Types

typedef NSNumber EndpointId;

struct EndpointsStruct {
    __unsafe_unretained NSString* const Forge;
    __unsafe_unretained NSString* const Source;
    __unsafe_unretained NSString* const Temporary;
    __unsafe_unretained NSString* const Permanent;
    __unsafe_unretained NSString* const Documents;
};

@interface EndpointIds : NSObject

@property (readonly) EndpointId* Forge;
@property (readonly) EndpointId* Source;
@property (readonly) EndpointId* Temporary;
@property (readonly) EndpointId* Permanent;
@property (readonly) EndpointId* Documents;

@end

@interface Directories : NSObject

@property (readonly) NSURL* Forge;
@property (readonly) NSURL* Source;
@property (readonly) NSURL* Temporary;
@property (readonly) NSURL* Permanent;
@property (readonly) NSURL* Documents;

@end


#pragma mark ForgeStorage

@interface ForgeStorage : NSObject

@property (class, readonly) struct EndpointsStruct Endpoints;
@property (class, readonly) EndpointIds* EndpointIds;
@property (class, readonly) Directories* Directories;

+ (NSString*)   endpointForId:(EndpointId*)endpointId;
+ (EndpointId*) idForEndpoint:(NSString*)endpoint;

+ (NSURL*)    nativeURL:(ForgeFile*)file;   // suitable for consumption by Cocoa
+ (NSURL*)    scriptURL:(ForgeFile*)file;   // suitable for consumption by Embedded Server / WebView
+ (NSString*) scriptPath:(ForgeFile*)file;  // suitable for consumption by Embedded Server / WebView

+ (NSDictionary*) getSizeInformation:(NSError**)error;

+ (NSString*)temporaryFileNameWithExtension:(NSString*)extension;

@end


NS_ASSUME_NONNULL_END
