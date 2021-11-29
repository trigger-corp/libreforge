import Foundation

//
// Here you can implement event listeners.
// These are functions which will get called when certain native events happen.
//

// The example below passes an event through to JavaScript when the application is resumed.
public class native_EventListener: ForgeEventListener {
    public dynamic override class func applicationWillEnterForeground(_ application: UIApplication) {
        ForgeApp.shared().event("native.resume", withParam: nil);
    }
}
