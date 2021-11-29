#import <Foundation/Foundation.h>

@interface ForgeMigration : NSObject

@property (class, nonatomic, assign, readonly) NSURL* OldWebViewStorageRoot;
@property (class, nonatomic, assign, readonly) NSURL* OldLocalStorageDir;
@property (class, nonatomic, assign, readonly) NSURL* OldWebSQLDir;
@property (class, nonatomic, assign, readonly) NSURL* OldIndexedDBDir;

@property (class, nonatomic, assign, readonly) NSURL* WKWebViewStorageRoot;
@property (class, nonatomic, assign, readonly) NSURL* WKLocalStorageDir;
@property (class, nonatomic, assign, readonly) NSURL* WKWebSQLDir;
@property (class, nonatomic, assign, readonly) NSURL* WKIndexedDBDir;


+ (NSURL*)OldWebViewStorageRoot;
+ (NSURL*)OldLocalStorageDir;
+ (NSURL*)OldWebSQLDir;
+ (NSURL*)OldIndexedDBDir;

+ (NSURL*)WKWebViewStorageRoot;
+ (NSURL*)WKLocalStorageDir;
+ (NSURL*)WKWebSQLDir;
+ (NSURL*)WKIndexedDBDir;


+ (void)MoveWKWebViewStorageToOldWebView;
+ (void)MoveOldWebViewStorageToWKWebView;
+ (void)MoveFileSchemeStorageToHttpScheme; // Supports both OldWebView and WKWebView

@end
