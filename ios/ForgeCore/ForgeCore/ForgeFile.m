#import <CoreServices/CoreServices.h>
#import <UniformTypeIdentifiers/UTType.h>

#import "NSData+MimeTypeForData.h"

#import "ForgeError.h"
#import "ForgeLog.h"

#import "ForgeFile.h"


/** Object containing information about a file with methods to access it. */
@implementation ForgeFile


#pragma mark life-cycle

+ (ForgeFile*)withEndpointId:(EndpointId*)endpointId resource:(NSString*)resource {
    ForgeFile *this = [[ForgeFile alloc] init];
    if (this != nil) {
        this->_endpointId = endpointId;
        this->_resource   = resource;
    }

    return this;
}


+ (ForgeFile*)withScriptObject:(NSDictionary*)scriptObject error:(NSError**)error {
    scriptObject = [ForgeFile parseScriptObject:scriptObject error:error];
    if (*error != nil) {
        return nil;
    }

    ForgeFile *this = [[ForgeFile alloc] init];
    if (this != nil) {
        this->_endpointId = scriptObject[@"_endpointId"];
        this->_resource   = scriptObject[@"resource"];
    }

    return this;
}


#pragma mark helpers

+ (NSDictionary*) parseScriptObject:(NSDictionary*)properties error:(NSError**)error {
    NSString *endpoint = properties[@"endpoint"];
    if (endpoint == nil) {
        *error = [NSError errorWithDomain:ForgeErrorDomain
                                   code:ForgeFileErrorCode
                               userInfo:@{
           NSLocalizedDescriptionKey:@"File object requires property: endpoint"
        }];
        return nil;
    }

    EndpointId* endpointId = [ForgeStorage idForEndpoint:endpoint];
    if (endpointId == nil) {
        *error = [NSError errorWithDomain:ForgeErrorDomain
                                   code:ForgeFileErrorCode
                               userInfo:@{
            NSLocalizedDescriptionKey:[NSString stringWithFormat:@"File object refers to invalid endpoint: %@", endpoint]
        }];
        return nil;
    }

    NSString *resource = properties[@"resource"];
    if (resource == nil) {
        *error = [NSError errorWithDomain:ForgeErrorDomain
                                   code:ForgeFileErrorCode
                               userInfo:@{
           NSLocalizedDescriptionKey:@"File object requires property: resource"
        }];
        return nil;
    }

    NSMutableDictionary *ret = [NSMutableDictionary dictionaryWithDictionary:properties];
    [ret addEntriesFromDictionary:@{
        @"_endpointId": endpointId
    }];

    return ret;
}

/** Return a dictionary to be converted to JSON File object */
- (NSDictionary*) toScriptObject {
   return @{
        @"endpoint": [ForgeStorage endpointForId:self->_endpointId],
        @"resource": self->_resource
    };
}


#pragma mark properties

- (NSString*) endpoint {
    return [ForgeStorage endpointForId:self->_endpointId];
}

/** Return the files mime-type (if available) */
- (NSString*) mimeType {
    NSString *extension = self->_resource.pathExtension;
    if (extension == nil) {
        NSData *data = [NSData dataWithContentsOfURL:[ForgeStorage nativeURL:self]];
        return [NSData mimeTypeForData:data];
    }

    NSString *mimeType = nil;
    if (@available(iOS 14.0, *)) {
        UTType *type = [UTType typeWithFilenameExtension:extension];
        mimeType = type.preferredMIMEType;
    } else {
        CFStringRef type = UTTypeCreatePreferredIdentifierForTag(kUTTagClassFilenameExtension, (__bridge CFStringRef)extension, NULL);
        mimeType = (__bridge_transfer NSString*)UTTypeCopyPreferredTagWithClass(type, kUTTagClassMIMEType);
    }
    return mimeType;
}


#pragma mark interface

/** Whether or not the referenced file exists */
- (void) exists:(ForgeFileExistsResultBlock)resultBlock {
    NSURL *url = [ForgeStorage nativeURL:self];
    BOOL exists = [NSFileManager.defaultManager fileExistsAtPath:url.path];
    resultBlock(exists);
}


/** Access file info */
- (void) attributes:(ForgeFileInfoResultBlock)resultBlock errorBlock:(ForgeFileErrorDescriptionBlock)errorBlock {
    dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
        NSFileManager *fileManager = NSFileManager.defaultManager;
        NSURL *url = [ForgeStorage nativeURL:self];
        NSError *error = nil;

        NSDictionary *attributes = [fileManager attributesOfItemAtPath:url.path error:&error];
        if (error != nil) {
            errorBlock([NSString stringWithFormat:@"Failed to obtain file attributes: %@", error.localizedDescription]);
            return;
        }

        unsigned long long size = [attributes fileSize];
        NSDate *added = [attributes fileModificationDate];
        NSDate *modified = [attributes fileModificationDate];
        if (added == nil || modified == nil) {
            errorBlock([NSString stringWithFormat:@"File not found: %@", [self toScriptObject]]);
            return;
        }

        NSDateFormatter *fmt = [[NSDateFormatter alloc] init];
        [fmt setTimeZone:[NSTimeZone timeZoneWithAbbreviation:@"UTC"]];
        [fmt setDateFormat:@"yyyy-MM-dd'T'HH:mm:ss'Z'"];

        resultBlock(@{
            @"size": [NSNumber numberWithUnsignedLongLong:size],
            @"added": [fmt stringFromDate:added],
            @"modified": [fmt stringFromDate:modified],
            @"mimetype": self.mimeType,

            @"date": [fmt stringFromDate:modified], // deprecated
        });
    });
}


/** Access the files contents */
- (void) contents:(ForgeFileContentsResultBlock)resultBlock errorBlock:(ForgeFileErrorBlock)errorBlock {
    NSURL *url = [ForgeStorage nativeURL:self];
    resultBlock([NSData dataWithContentsOfURL:url]);
}


/** Attempt to remove the file */
- (void) remove:(ForgeFileResultBlock)resultBlock errorBlock:(ForgeFileErrorBlock)errorBlock {
    NSError *error = nil;

    // restrict destructive operations to temporary, permanent and document endpoints only
    NSArray *mutableEndpoints = @[
        ForgeStorage.EndpointIds.Temporary,
        ForgeStorage.EndpointIds.Permanent,
        ForgeStorage.EndpointIds.Documents
    ];

    if (![mutableEndpoints containsObject:self.endpointId]) {
        NSString *description = [NSString stringWithFormat:@"Cannot remove file from protected endpoint: %@", self.endpoint];
        error = [NSError errorWithDomain:ForgeErrorDomain
                                    code:ForgeFileErrorCode
                                userInfo:@{
            NSLocalizedDescriptionKey:description
        }];
        return errorBlock(error);
    }

    bool removed = [NSFileManager.defaultManager removeItemAtURL:[ForgeStorage nativeURL:self] error:&error];
    if (error != nil) {
        return errorBlock(error);

    } else if (removed == NO) {
        error = [NSError errorWithDomain:ForgeErrorDomain
                                    code:ForgeFileErrorCode
                                userInfo:@{
            NSLocalizedDescriptionKey:@"Failed to remove file"
        }];
        return errorBlock(error);

    }

    return resultBlock();
}

@end
