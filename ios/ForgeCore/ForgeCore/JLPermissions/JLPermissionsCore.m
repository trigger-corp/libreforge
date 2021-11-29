//
//  JLPermissionCore.m
//
//  Created by Joseph Laws on 11/3/14.
//  Copyright (c) 2014 Joe Laws <joe.laws@gmail.com>
//
//  Permission is hereby granted, free of charge, to any person obtaining a copy
//  of this software and associated documentation files (the "Software"), to deal
//  in the Software without restriction, including without limitation the rights
//  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//  copies of the Software, and to permit persons to whom the Software is
//  furnished to do so, subject to the following conditions:
//
//  The above copyright notice and this permission notice shall be included in
//  all copies or substantial portions of the Software.
//
//  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
//  THE SOFTWARE.
//

#import <ForgeCore/ForgeApp.h>

#import "JLPermissionsCore.h"

// TODO support this: https://github.com/danielebogo/DBPrivacyHelper
// #import <DBPrivacyHelper/DBPrivateHelperController.h>
#define IS_IOS_8 ([[[UIDevice currentDevice] systemVersion] floatValue] >= 8.0 ? 1 : 0)

@implementation JLPermissionsCore

- (instancetype)init {
    self = [super init];
    if (self) {
        [self setExtraAlertEnabled:YES];
    }
    return self;
}

- (NSString *)defaultTitle:(NSString *)authorizationType {
    if (self.getRationale != nil) {
        return self.getRationale;
    } else {
        return [NSString stringWithFormat:@"\"%@\" Would Like to Access Your %@", [self appName], authorizationType];
    }
}

- (NSString *)defaultMessage {
    return nil;
}

- (NSString *)defaultCancelTitle {
    return @"No Thanks";
}

- (NSString *)defaultGrantTitle {
    return @"Okay";
}

- (NSString *)appName {
    return [[NSBundle mainBundle] objectForInfoDictionaryKey:@"CFBundleDisplayName"];
}

- (UIViewController *)reenableViewController {
    // TODO See above
    /*DBPrivacyType privacyType;
     switch ([self permissionType]) {
     case JLPermissionCalendar:
     privacyType = DBPrivacyTypeCalendars;
     break;
     case JLPermissionCamera:
     privacyType = DBPrivacyTypeCamera;
     break;
     case JLPermissionContacts:
     privacyType = DBPrivacyTypeContacts;
     break;
     case JLPermissionFacebook:
     privacyType = DBPrivacyTypeFacebook;
     break;
     case JLPermissionHealth:
     privacyType = DBPrivacyTypeHealth;
     break;
     case JLPermissionLocation:
     privacyType = DBPrivacyTypeLocation;
     break;
     case JLPermissionMicrophone:
     privacyType = DBPrivacyTypeMicrophone;
     break;
     case JLPermissionNotification:
     privacyType = DBPrivacyTypeNotifications;
     break;
     case JLPermissionPhotos:
     privacyType = DBPrivacyTypePhoto;
     break;
     case JLPermissionReminders:
     privacyType = DBPrivacyTypeReminders;
     break;
     case JLPermissionTwitter:
     privacyType = DBPrivacyTypeTwitter;
     break;
     }
     DBPrivateHelperController *vc = [DBPrivateHelperController helperForType:privacyType];
     vc.snapshot = [self snapshot];
     vc.modalTransitionStyle = UIModalTransitionStyleCrossDissolve;
     return vc;*/
    return NULL;
}

- (UIImage *)snapshot {
    id<UIApplicationDelegate> appDelegate = [[UIApplication sharedApplication] delegate];

    UIGraphicsBeginImageContextWithOptions(appDelegate.window.bounds.size, NO,
                                           appDelegate.window.screen.scale);

    [appDelegate.window drawViewHierarchyInRect:appDelegate.window.bounds afterScreenUpdates:NO];

    UIImage *snapshotImage = UIGraphicsGetImageFromCurrentImageContext();

    UIGraphicsEndImageContext();

    return snapshotImage;
}

- (void)displayReenableAlert {
    NSString *message = [NSString stringWithFormat:@"Please go to Settings -> Privacy -> "
                         @"%@ to re-enable %@'s access.",
                         [self permissionName], [self appName]];
    UIAlertController *alert = [UIAlertController alertControllerWithTitle:nil
                                                                   message:message
                                                            preferredStyle:UIAlertControllerStyleAlert];
    [alert addAction:[UIAlertAction actionWithTitle:@"Ok"
                                              style:UIAlertActionStyleCancel
                                            handler:nil]];
    dispatch_async(dispatch_get_main_queue(), ^{
        [ForgeApp.sharedApp.viewController presentViewController:alert animated:YES completion:nil];
    });
}

- (NSString *)permissionName {
    switch ([self permissionType]) {
        case JLPermissionCalendar:
            return @"Calendar";
        case JLPermissionCamera:
            return @"Camera";
        case JLPermissionContacts:
            return @"Contacts";
        case JLPermissionFacebook:
            return @"Facebook";
        case JLPermissionHealth:
            return @"Health";
        case JLPermissionLocation:
            return @"Location";
        case JLPermissionMicrophone:
            return @"Microphone";
        case JLPermissionNotification:
            return @"Notification";
        case JLPermissionPhotos:
            return @"Photos";
        case JLPermissionReminders:
            return @"Reminders";
        case JLPermissionTwitter:
            return @"Twitter";
    }
}

- (NSError *)userDeniedError {
    return [NSError errorWithDomain:@"UserDenied" code:JLPermissionUserDenied userInfo:nil];
}

- (NSError *)previouslyDeniedError {
    return [NSError errorWithDomain:@"SystemDenied" code:JLPermissionSystemDenied userInfo:nil];
}

- (NSError *)systemDeniedError:(NSError *)error {
    return [NSError errorWithDomain:@"SystemDenied"
                               code:JLPermissionSystemDenied
                           userInfo:[error userInfo]];
}

- (void)displayAppSystemSettings {
    if (IS_IOS_8 && UIApplicationOpenSettingsURLString != NULL) {
        NSURL *appSettings = [NSURL URLWithString:UIApplicationOpenSettingsURLString];
        [[UIApplication sharedApplication] openURL:appSettings options:@{} completionHandler:nil];
    }
}

#pragma mark - Abstract methods

- (JLPermissionType)permissionType {
    @throw [NSException
            exceptionWithName:NSInternalInconsistencyException
            reason:[NSString stringWithFormat:@"You must override %@ in a subclass",
                    NSStringFromSelector(_cmd)]
            userInfo:nil];
}

- (JLAuthorizationStatus)authorizationStatus {
    @throw [NSException
            exceptionWithName:NSInternalInconsistencyException
            reason:[NSString stringWithFormat:@"You must override %@ in a subclass",
                    NSStringFromSelector(_cmd)]
            userInfo:nil];
}

- (void)actuallyAuthorize {
    @throw [NSException
            exceptionWithName:NSInternalInconsistencyException
            reason:[NSString stringWithFormat:@"You must override %@ in a subclass",
                    NSStringFromSelector(_cmd)]
            userInfo:nil];
}

- (void)canceledAuthorization:(NSError *)error {
    @throw [NSException
            exceptionWithName:NSInternalInconsistencyException
            reason:[NSString stringWithFormat:@"You must override %@ in a subclass",
                    NSStringFromSelector(_cmd)]
            userInfo:nil];
}

- (void)authorize:(AuthorizationHandler)completion {
    @throw [NSException
            exceptionWithName:NSInternalInconsistencyException
            reason:[NSString stringWithFormat:@"You must override %@ in a subclass",
                    NSStringFromSelector(_cmd)]
            userInfo:nil];
}


/* TODO test

#pragma mark - UIAlertViewDelegate

- (void)alertView:(UIAlertView *)alertView clickedButtonAtIndex:(NSInteger)buttonIndex {
    BOOL canceled = (buttonIndex == alertView.cancelButtonIndex);
    dispatch_async(dispatch_get_main_queue(), ^{
        if (canceled) {
            NSError *error =
            [NSError errorWithDomain:@"UserDenied" code:JLPermissionUserDenied userInfo:nil];
            [self canceledAuthorization:error];
        } else {
            [self actuallyAuthorize];
        }
    });
}*/

@end
