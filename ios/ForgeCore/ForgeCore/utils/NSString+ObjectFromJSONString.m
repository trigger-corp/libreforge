#import "NSString+ObjectFromJSONString.h"
#import "NSData+ObjectFromJSONData.h"

@implementation NSString (ObjectFromJSONString)

- (id)objectFromJSONString
{
    NSData *jsonData = [self dataUsingEncoding:NSUTF8StringEncoding];
    return [jsonData objectFromJSONData];
}

@end
