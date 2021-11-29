#import "ForgeUtil.h"


@implementation ForgeUtil

+ (BOOL)isIphone {
    if ([[UIDevice currentDevice].model isEqualToString:@"iPhone Simulator"]) {
        return YES;
    } else {
        return UI_USER_INTERFACE_IDIOM() == UIUserInterfaceIdiomPhone;
    }
}

+ (BOOL)isIphone_xr {
    return [[UIScreen mainScreen] nativeBounds].size.height == 1792.;
}


+ (BOOL)isIpad {
    if ([[UIDevice currentDevice].model isEqualToString:@"iPhone Simulator"]) {
        return NO;
    } else if ([[UIDevice currentDevice].model isEqualToString:@"iPad Simulator"]) {
        return YES;
    } else {
        return [[UIDevice currentDevice] userInterfaceIdiom] == UIUserInterfaceIdiomPad;
    }
}

+ (BOOL)isDeviceWithNotch {
    if (@available(iOS 11.0, *)) {
        // with notch: 44.0 on iPhone X, XS, XS Max, XR.
        // without notch: 20.0 on iPhone 8 on iOS 12+.
        return UIApplication.sharedApplication.delegate.window.safeAreaInsets.top > 20;
    }
    return NO;
}


+ (BOOL) url:(NSString*)url matchesPattern:(NSString*)pattern {
	NSURL *parsed = [NSURL URLWithString:url];
	if (parsed != nil) {
		if ([pattern isEqualToString:@"<all_urls>"]) {
			return YES;
		}

		// Check scheme
		NSString *patternScheme = [[pattern componentsSeparatedByString:@"://"] objectAtIndex:0];
		if (![patternScheme isEqualToString:@"*"] && ![patternScheme isEqualToString:[parsed scheme]]) {
			return NO;
		}

		// Check host
		NSString *patternHostPath = [[pattern componentsSeparatedByString:@"://"] objectAtIndex:1];
		NSString *patternHost = [[patternHostPath componentsSeparatedByString:@"/"] objectAtIndex:0];
		if (![patternHost isEqualToString:@"*"]) {
			if ([patternHost hasPrefix:@"*."]) {
				if (![[parsed host] hasSuffix:[@"." stringByAppendingString:[patternHost substringFromIndex:2]]] && ![[patternHost substringFromIndex:2] isEqualToString:[parsed host]]) {
					return NO;
				}
			} else {
				if (![patternHost isEqualToString:[parsed host]]) {
					return NO;
				}
			}
		}

		// Check path
		NSString *patternPath = [[patternHostPath substringFromIndex:[patternHost length]] stringByReplacingOccurrencesOfString:@"*" withString:@".*"];
		if ([patternPath length] > 0) {
			NSRegularExpression *regex = [NSRegularExpression regularExpressionWithPattern:patternPath options:NSRegularExpressionCaseInsensitive error:nil];
			if ([regex numberOfMatchesInString:[parsed path] options:0 range:NSMakeRange(0, [[parsed path] length])] == 0) {
				return NO;
			}
		}
		return YES;
	} else {
		return NO;
	}
}


+ (NSData*)sendSynchronousRequest:(NSURLRequest*)request returningResponse:(NSURLResponse**)response error:(NSError**)error {
    __block NSData *blockData = nil;
    @try {
        __block NSURLResponse *blockResponse = nil;
        __block NSError *blockError = nil;

        dispatch_group_t group = dispatch_group_create();
        dispatch_group_enter(group);

        NSURLSession *session = [NSURLSession sharedSession];
        [[session dataTaskWithRequest:request completionHandler:^(NSData * _Nullable subData, NSURLResponse * _Nullable subResponse, NSError * _Nullable subError) {
            blockData = subData;
            blockError = subError;
            blockResponse = subResponse;
            dispatch_group_leave(group);
        }] resume];

        dispatch_group_wait(group,  DISPATCH_TIME_FOREVER);

        *error = blockError;
        *response = blockResponse;

    } @catch (NSException *exception) {
        NSLog(@"%@", exception.description);
    } @finally {
        return blockData;
    }
}

@end
