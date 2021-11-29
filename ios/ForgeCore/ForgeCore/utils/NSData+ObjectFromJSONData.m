#import "NSData+ObjectFromJSONData.h"

@implementation NSData (ObjectFromJSONData)

- (id)objectFromJSONData
{
    NSError *decodingError = nil;
    id object = [NSJSONSerialization JSONObjectWithData:self
                                                options:NSJSONReadingAllowFragments
                                                  error:&decodingError];

    if (object == nil && decodingError != nil) {
        NSLog(@"Error decoding JSON data");
    }

    return object;
}

@end
