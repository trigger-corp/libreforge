#import "ForgeAppDelegate.h"
#import "ForgeJSBridge.h"
#import "ForgeApp.h"
#import "ForgeLog.h"
#import <objc/objc.h>
#import <objc/objc-runtime.h>

@implementation ForgeAppDelegate

- (id)init
{
    self = [super init];
    if (self) {
		[[ForgeApp sharedApp] setAppDelegate:self];

		NSMutableSet *enabledModules = [[NSMutableSet alloc] init];

		// Required modules
		[enabledModules addObject:@"logging"];
		[enabledModules addObject:@"tools"];

		NSDictionary *modules = (NSDictionary*)[[[ForgeApp sharedApp] appConfig] objectForKey:@"modules"];
		if (modules != nil) {
			[enabledModules addObjectsFromArray:[modules allKeys]];
		}

		for (NSString *module in enabledModules) {
			// Event listener
			Class moduleEventListener = NSClassFromString([NSString stringWithFormat:@"%@_EventListener", module]);

			if (moduleEventListener) {
				[[ForgeApp sharedApp].eventListeners addObject:moduleEventListener];
			}

			// API Methods
			NSString *moduleAPI = [NSString stringWithFormat:@"%@_API", module];
			unsigned int methodCount;
			Method *methods = class_copyMethodList(object_getClass(NSClassFromString(moduleAPI)), &methodCount);
			for (int i = 0; i < methodCount; i++) {
				SEL name = method_getName(methods[i]);
				NSString *selector = NSStringFromSelector(name);
				NSString *selectorPrefix = [selector substringToIndex:[selector rangeOfString:@":"].location];
				NSString *jsMethod = [NSString stringWithFormat:@"%@.%@", module, selectorPrefix];
				[[ForgeApp sharedApp] addAPIMethod:jsMethod withClass:moduleAPI andSelector:selector];
			}
			free(methods);

			if ([module isEqualToString:@"inspector"]) {
				// Enable extra inspector events for debugging.
				[[ForgeApp sharedApp] setInspectorEnabled:YES];
			}
		}
    }
    return self;
}

- (void)applicationDidFinishLaunching:(NSNotification *)aNotification {
	[[self window] setTitle:[[[NSBundle mainBundle] infoDictionary] objectForKey:@"CFBundleName"]];

	[[ForgeApp sharedApp] setWebView:[self webView]];
	NSString *path = [[NSBundle mainBundle] pathForResource:@"assets/src/index.html" ofType:@""];

	[[[self webView] mainFrame] loadRequest:[NSURLRequest requestWithURL:[[NSURL alloc] initWithScheme:@"file" host:@"" path:path]]];
}

- (void)webView:(WebView *)webView didClearWindowObject:(WebScriptObject *)windowObject forFrame:(WebFrame *)frame {
	[windowObject setValue:[[ForgeJSBridge alloc] init] forKey:@"__forge"];
}

- (BOOL)applicationShouldHandleReopen:(NSApplication *)sender hasVisibleWindows:(BOOL)flag {
	if(!flag){
        [[self window] makeKeyAndOrderFront:self];
    }

	return YES;
}

// Disable context menu
- (NSArray *)webView:(WebView *)sender contextMenuItemsForElement:(NSDictionary *)element defaultMenuItems:(NSArray *)defaultMenuItems {
	return nil;
}

- (void)webView:(WebView *)webView decidePolicyForNavigationAction:(NSDictionary *)actionInformation request:(NSURLRequest *)request frame:(WebFrame *)frame decisionListener:(id<WebPolicyDecisionListener>)listener {
	if ([frame isEqual:[[[ForgeApp sharedApp] webView] mainFrame]]) {
		if ([[[request URL] scheme] isEqualToString:@"about"]) {

		} else if (![[[request URL] scheme] isEqualToString:@"file"]) {
			// Open external links in browser
			[[NSWorkspace sharedWorkspace] openURL:[request URL]];
			[listener ignore];
			return;
		}
	}
	[listener use];
}

- (void)webView:(WebView *)sender runJavaScriptAlertPanelWithMessage:(NSString *)message initiatedByFrame:(WebFrame *)frame {
	NSAlert *alert = [NSAlert alertWithMessageText:message defaultButton:@"OK" alternateButton:nil otherButton:nil informativeTextWithFormat:@""];
	[alert runModal];
}

- (BOOL)webView:(WebView *)sender runJavaScriptConfirmPanelWithMessage:(NSString *)message initiatedByFrame:(WebFrame *)frame {
	NSAlert *alert = [NSAlert alertWithMessageText:message defaultButton:@"OK" alternateButton:@"Cancel" otherButton:nil informativeTextWithFormat:@""];
	if ([alert runModal] == NSAlertDefaultReturn) {
		return YES;
	} else {
		return NO;
	}
}

- (NSString *)webView:(WebView *)sender runJavaScriptTextInputPanelWithPrompt:(NSString *)prompt defaultText:(NSString *)defaultText initiatedByFrame:(WebFrame *)frame {
	NSAlert *alert = [NSAlert alertWithMessageText:prompt defaultButton:@"OK" alternateButton:@"Cancel" otherButton:nil informativeTextWithFormat:@""];

	NSTextField *input = [[NSTextField alloc] initWithFrame:NSMakeRect(0, 0, 300, 24)];
	[input setStringValue:defaultText];
	[alert setAccessoryView:input];

	if ([alert runModal] == NSAlertDefaultReturn) {
		[input validateEditing];
		return [input stringValue];
	} else {
		return nil;
	}
}

- (void)webView:(WebView *)webView addMessageToConsole:(NSDictionary*)message {
	[ForgeLog w:[message description]];
}

@end
