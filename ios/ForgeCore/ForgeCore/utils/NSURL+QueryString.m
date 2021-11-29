#import "NSURL+QueryString.h"

@implementation NSURL (QueryString)

- (NSDictionary *)queryAsDictionary {
    NSMutableDictionary *dict = [[NSMutableDictionary alloc] initWithCapacity:6];
    NSArray *pairs = [[[self query] stringByTrimmingCharactersInSet:[NSCharacterSet characterSetWithCharactersInString:@"?&"]] componentsSeparatedByString:@"&"];

    for (NSString *pair in pairs) {
        NSArray *elements = [pair componentsSeparatedByString:@"="];
        NSString *key = [[elements objectAtIndex:0] stringByRemovingPercentEncoding];
        NSString *val = [[elements objectAtIndex:1] stringByRemovingPercentEncoding];

        [dict setObject:val forKey:key];
    }
    return dict;
}

@end
