import Foundation

//
// Here you can implement your API methods which can be called from JavaScript
// an example method is included below to get you started.
//

// This will be callable from JavaScript as 'native.showAlert'
// it will require a parameter called text
public class native_API: NSObject {
    public dynamic class func showAlert(task: ForgeTask, text: String) {
        if (text.characters.count == 0) {
            task.error("You must enter a message");
        }
        let alert: UIAlertView = UIAlertView();
        alert.message = text;
        alert.delegate = nil;
        alert.addButton(withTitle: "OK");
        alert.show();
        task.success(nil);
    }
}
