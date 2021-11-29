//
//  JLPermissionCore.h
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

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>

typedef NS_ENUM(NSInteger, JLAuthorizationErrorCode) {
  JLPermissionUserDenied = 42,
  JLPermissionSystemDenied
};

typedef NS_ENUM(NSInteger, JLAuthorizationStatus) {
  JLPermissionNotDetermined = 0,
  JLPermissionDenied,
  JLPermissionAuthorized
};

typedef NS_ENUM(NSInteger, JLPermissionType) {
  JLPermissionCalendar = 0,
  JLPermissionCamera,
  JLPermissionContacts,
  JLPermissionFacebook,
  JLPermissionHealth,
  JLPermissionLocation,
  JLPermissionMicrophone,
  JLPermissionNotification,
  JLPermissionPhotos,
  JLPermissionReminders,
  JLPermissionTwitter,
};

NS_ASSUME_NONNULL_BEGIN
typedef void (^AuthorizationHandler)(BOOL granted, NSError *__nullable error);
typedef void (^NotificationAuthorizationHandler)(NSString *__nullable deviceID,
                                                 NSError *__nullable error);

@interface JLPermissionsCore : NSObject<UIAlertViewDelegate>

/**
 * A Boolean property that indicates whether the extra alert view will be shown
 * before the library actually requests permissions to the system.
 */
@property(nonatomic, getter=isExtraAlertEnabled) BOOL extraAlertEnabled;

/**
 * A NSString property that, if set, will replace the default message shown
 * before the library actually requests permissions to the system.
 */
@property(nonatomic, getter=getRationale) NSString* rationale;


/**
 * @return whether or not user has granted access to the calendar
 */
- (JLAuthorizationStatus)authorizationStatus;

/**
 * Override to perform the authorization call
 */
- (void)authorize:(AuthorizationHandler)completion;

/**
 * Displays a dialog telling the user how to re-enable the permission in
 * the Settings application
 */
- (void)displayReenableAlert;

/**
 * A view controller telling the user how to re-enable the permission in
 * the Settings application or nil if one doesnt exist.
 */
- (UIViewController *__nullable)reenableViewController;

/**
 * The type of permission.
 */
- (JLPermissionType)permissionType;

/**
 * Opens the application system settings dialog if running on iOS 8.
 */
- (void)displayAppSystemSettings;

@end
NS_ASSUME_NONNULL_END
