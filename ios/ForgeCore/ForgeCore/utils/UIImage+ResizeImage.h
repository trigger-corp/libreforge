#import <UIKit/UIKit.h>

@interface UIImage (ResizeImage)

- (UIImage*)imageWithWidth:(float)maxwidth andHeight:(float)maxheight;
- (UIImage*)imageWithWidth:(float)maxwidth andHeight:(float)maxheight andRetina:(BOOL)allowRetina;

@end
