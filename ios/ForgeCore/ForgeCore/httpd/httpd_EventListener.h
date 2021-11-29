#import <Criollo/CRHTTPServer.h>

#import "ForgeEventListener.h"


@interface httpd_EventListener : ForgeEventListener

+ (NSURL*) getURL;
+ (void) restartServer;

@end


@interface ServerDelegate : NSObject <CRServerDelegate>

@end
