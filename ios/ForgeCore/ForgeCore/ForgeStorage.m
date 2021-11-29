#import "ForgeLog.h"
#import "ForgeApp.h"
#import "ForgeFile.h"

#import "httpd_EventListener.h"

#import "ForgeStorage.h"


#pragma mark Types

const struct EndpointsStruct EndpointsInstance = {
    .Forge     = @"/forge",
    .Source    = @"/src",
    .Temporary = @"/temporary",
    .Permanent = @"/permanent",
    .Documents = @"/documents",
};


@implementation EndpointIds

- (EndpointIds*)init {
    if (self = [super init]) {
        self->_Forge     = @0;
        self->_Source    = @1;
        self->_Temporary = @2;
        self->_Permanent = @3;
        self->_Documents = @4;
    }
    return self;
}

+ (EndpointIds*)instance {
    static EndpointIds *sharedInstance = nil;
    static dispatch_once_t once;
    dispatch_once(&once, ^{
        sharedInstance = [[EndpointIds alloc] init];
    });
    return sharedInstance;
}

+ (EndpointId*)Forge     { return EndpointIds.instance->_Forge; }
+ (EndpointId*)Source    { return EndpointIds.instance->_Source; }
+ (EndpointId*)Temporary { return EndpointIds.instance->_Temporary; }
+ (EndpointId*)Permanent { return EndpointIds.instance->_Permanent; }
+ (EndpointId*)Documents { return EndpointIds.instance->_Documents; }

@end


@implementation Directories

+ (Directories*)instance {
    static Directories *sharedInstance = nil;
    static dispatch_once_t once;
    dispatch_once(&once, ^{
        sharedInstance = [[Directories alloc] init];
    });
    return sharedInstance;
}

- (NSURL*) Forge {
    NSURL* assetsFolderLocation = [ForgeApp.sharedApp assetsFolderLocationWithPrefs:NSUserDefaults.standardUserDefaults];
    return [assetsFolderLocation URLByAppendingPathComponent:@"forge"];
}

- (NSURL*) Source {
    NSURL* assetsFolderLocation = [ForgeApp.sharedApp assetsFolderLocationWithPrefs:NSUserDefaults.standardUserDefaults];
    return [assetsFolderLocation URLByAppendingPathComponent:@"src"];
}

- (NSURL*) Temporary {
    NSURL* url = [[NSFileManager defaultManager] temporaryDirectory];
    url = [url URLByAppendingPathComponent:@"forgecore" isDirectory:YES];
    if (![NSFileManager.defaultManager fileExistsAtPath:[url path]]) {
        NSError *error = nil;
        [[NSFileManager defaultManager] createDirectoryAtURL:url withIntermediateDirectories:NO attributes:nil error:&error];
        if (error != nil) {
            [ForgeLog w:[NSString stringWithFormat:@"Failed to create temporary directory: %@", error]];
        }
    }
    return url;
}

- (NSURL*) Permanent {
    NSURL* url = ForgeApp.sharedApp.applicationSupportDirectory;
    url = [url URLByAppendingPathComponent:@"forgecore" isDirectory:YES];
    if (![NSFileManager.defaultManager fileExistsAtPath:[url path]]) {
        NSError *error = nil;
        [[NSFileManager defaultManager] createDirectoryAtURL:url withIntermediateDirectories:NO attributes:nil error:&error];
        if (error != nil) {
            [ForgeLog w:[NSString stringWithFormat:@"Failed to create temporary directory: %@", error]];
        }
    }
    return url;
}

- (NSURL*) Documents {
    NSError *error = nil;
    NSURL *url = [NSFileManager.defaultManager URLForDirectory:NSDocumentDirectory
                                                      inDomain:NSUserDomainMask
                                             appropriateForURL:nil
                                                        create:YES
                                                         error:&error];
    if (error != nil) {
        [ForgeLog w:[NSString stringWithFormat:@"Failed to obtain public directory: %@", error]];
    }
    return url;
}

@end


#pragma mark ForgeStorage

@implementation ForgeStorage

#pragma mark life-cycle

- (ForgeStorage*)init {
    if (self = [super init]) {
    }
    return self;
}

+ (ForgeStorage*)instance {
    static ForgeStorage *sharedInstance = nil;
    static dispatch_once_t once;
    dispatch_once(&once, ^{
        sharedInstance = [[ForgeStorage alloc] init];
    });
    return sharedInstance;
}


#pragma mark class properties

+ (struct EndpointsStruct) Endpoints {
    return EndpointsInstance;
}

+ (EndpointIds*) EndpointIds {
    return EndpointIds.instance;
}

+ (Directories*) Directories {
    return Directories.instance;
}


#pragma mark interface

+ (NSString*)endpointForId:(EndpointId*)endpointId {
    if ([endpointId isEqualToNumber:ForgeStorage.EndpointIds.Forge]) {
        return EndpointsInstance.Forge;
    } else if ([endpointId isEqualToNumber:ForgeStorage.EndpointIds.Source]) {
        return EndpointsInstance.Source;
    } else if ([endpointId isEqualToNumber:ForgeStorage.EndpointIds.Temporary]) {
        return EndpointsInstance.Temporary;
    } else if ([endpointId isEqualToNumber:ForgeStorage.EndpointIds.Permanent]) {
        return EndpointsInstance.Permanent;
    } else if ([endpointId isEqualToNumber:ForgeStorage.EndpointIds.Documents]) {
        return EndpointsInstance.Documents;
    }
    [ForgeLog e:[NSString stringWithFormat:@"ERROR: Invalid endpointId: %@", endpointId]];
    return nil;
}


+ (EndpointId*)idForEndpoint:(NSString*)endpoint {
    if ([endpoint isEqualToString:EndpointsInstance.Forge]) {
        return ForgeStorage.EndpointIds.Forge;
    } else if ([endpoint isEqualToString:EndpointsInstance.Source]) {
        return ForgeStorage.EndpointIds.Source;
    } else if ([endpoint isEqualToString:EndpointsInstance.Temporary]) {
        return ForgeStorage.EndpointIds.Temporary;
    } else if ([endpoint isEqualToString:EndpointsInstance.Permanent]) {
        return ForgeStorage.EndpointIds.Permanent;
    } else if ([endpoint isEqualToString:EndpointsInstance.Documents]) {
        return ForgeStorage.EndpointIds.Documents;
    }
    [ForgeLog e:[NSString stringWithFormat:@"ERROR: Invalid endpoint: %@", endpoint]];
    return nil;
}


// suitable for consumption by Cocoa
+ (NSURL*) nativeURL:(ForgeFile*)file {
    NSURL *url = nil;

    if ([file.endpointId isEqualToNumber:ForgeStorage.EndpointIds.Forge]) {
        url = ForgeStorage.Directories.Forge;
    } else if ([file.endpointId isEqualToNumber:ForgeStorage.EndpointIds.Source]) {
        url = ForgeStorage.Directories.Source;
    } else if ([file.endpointId isEqualToNumber:ForgeStorage.EndpointIds.Temporary]) {
        url = ForgeStorage.Directories.Temporary;
    } else if ([file.endpointId isEqualToNumber:ForgeStorage.EndpointIds.Permanent]) {
        url = ForgeStorage.Directories.Permanent;
    } else if ([file.endpointId isEqualToNumber:ForgeStorage.EndpointIds.Documents]) {
        url = ForgeStorage.Directories.Documents;
    } else {
        [ForgeLog e:[NSString stringWithFormat:@"ERROR: Invalid endpoint: %@ -> %@", [file toScriptObject], file.endpoint]];
        return nil;
    }

    return [url URLByAppendingPathComponent:file.resource];
}


// suitable for consumption by Embedded Server / WebView
+ (NSURL*) scriptURL:(ForgeFile*)file {
    NSURL *url = [httpd_EventListener getURL];
    NSURL *baseURL = [NSURL URLWithString:@"/" relativeToURL:url].absoluteURL;

    NSString *scriptPath = [ForgeStorage scriptPath:file];
    NSMutableArray *pathComponents = [NSMutableArray arrayWithArray:scriptPath.pathComponents];
    if ([pathComponents.firstObject isEqualToString:@"/"]) {
        [pathComponents removeObjectAtIndex:0];
    }
    scriptPath = [pathComponents componentsJoinedByString:@"/"];

    return [baseURL URLByAppendingPathComponent:scriptPath];
}

// suitable for consumption by Embedded Server / WebView
+ (NSString*) scriptPath:(ForgeFile*)file {
    return [[ForgeStorage endpointForId:file.endpointId] stringByAppendingPathComponent:file.resource];
}


+ (NSDictionary*) getSizeInformation:(NSError**)error {
    NSArray *paths = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES);
    NSDictionary *attributes = [NSFileManager.defaultManager attributesOfFileSystemForPath:[paths lastObject]
                                                                                     error:error];
    if (*error != nil) {
        return nil;
    }

    NSNumber *appSize = [ForgeStorage _getDirectorySize:NSBundle.mainBundle.bundleURL];
    NSNumber *forgeSize = [ForgeStorage _getDirectorySize:ForgeStorage.Directories.Forge];
    NSNumber *sourceSize = [ForgeStorage _getDirectorySize:ForgeStorage.Directories.Source];
    NSNumber *temporarySize = [ForgeStorage _getDirectorySize:ForgeStorage.Directories.Temporary];
    NSNumber *permanentSize = [ForgeStorage _getDirectorySize:ForgeStorage.Directories.Permanent];
    NSNumber *documentsSize = [ForgeStorage _getDirectorySize:ForgeStorage.Directories.Documents];

    return @{
        @"total": [attributes objectForKey:NSFileSystemSize],
        @"free":  [attributes objectForKey:NSFileSystemFreeSize],
        @"app":   appSize,
        @"endpoints": @{
            @"forge": forgeSize,
            @"source": sourceSize,
            @"temporary": temporarySize,
            @"permanent": permanentSize,
            @"documents": documentsSize,
        },
        @"cache": temporarySize // deprecated
    };
}

+ (NSNumber*)_getDirectorySize:(NSURL*)url {
    unsigned long long int totalSize = 0;

    NSDirectoryEnumerator *enumerator = [NSFileManager.defaultManager enumeratorAtURL:url.URLByResolvingSymlinksInPath includingPropertiesForKeys:@[NSURLFileSizeKey] options:NSDirectoryEnumerationSkipsPackageDescendants errorHandler:^BOOL(NSURL* url, NSError* error) {
        return YES;
    }];

    for (NSURL* item in enumerator) {
        NSNumber* fileSize = nil;
        if ([item getResourceValue:&fileSize forKey:NSURLFileSizeKey error:nil]) {
            totalSize += fileSize.unsignedLongLongValue;
        }
    }

    return [NSNumber numberWithUnsignedLongLong:totalSize];
}



+ (NSString*)temporaryFileNameWithExtension:(NSString*)extension {
    NSString *uuid = [[NSUUID UUID] UUIDString];
    return [NSString stringWithFormat:@"%@.%@", uuid, extension];
}

@end

