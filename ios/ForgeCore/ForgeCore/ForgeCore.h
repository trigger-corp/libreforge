#import <Foundation/Foundation.h>

#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wquoted-include-in-framework-header"

    // Forge classes
    #import "ForgeError.h"
    #import "ForgeTask.h"
    #import "ForgeLog.h"
    #import "ForgeAppDelegate.h"
    #import "ForgeApp.h"
    #import "ForgeViewController.h"
    #import "ForgeAppDelegate.h"
    #import "ForgeEventListener.h"
    #import "ForgeFile.h"
    #import "ForgeStorage.h"
    #import "ForgeUtil.h"
    #import "BorderControl.h"
    #import "ForgeConstant.h"

    // Utilities
    #import "UIImage+ResizeImage.h"
    #import "NSData+Base64.h"
    #import "NSData+ObjectFromJSONData.h"
    #import "NSDictionary+JSONString.h"
    #import "NSString+ObjectFromJSONString.h"
    #import "NSURL+QueryString.h"
    #import "Reachability.h"
    #import "UIViewController+dismissViewControllerHelper.h"
    #import "NSFileManager+DoNotBackup.h"

#pragma clang diagnostic pop

// Currently missing from iOS SDK
#define NSFoundationVersionNumber_iOS_8_4 1144.17
