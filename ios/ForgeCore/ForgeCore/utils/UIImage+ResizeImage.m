#import "UIImage+ResizeImage.h"

#define radians(degrees) ( degrees * M_PI / 180 )

@implementation UIImage (ResizeImage)

- (UIImage*)imageWithWidth:(float)maxwidth andHeight:(float)maxheight {
	return [self imageWithWidth:maxwidth andHeight:maxheight andRetina:NO];
}

- (UIImage*)imageWithWidth:(float)maxwidth andHeight:(float)maxheight andRetina:(BOOL)allowRetina {
    CGSize imageSize = self.size;
	CGFloat width = imageSize.width;
	CGFloat height = imageSize.height;
	CGFloat targetWidth = (maxwidth != 0) ? maxwidth : width;
	CGFloat targetHeight = (maxheight != 0) ? maxheight : height;
    CGFloat scaleFactor = 0.0;

	CGFloat widthFactor = targetWidth / width;
	CGFloat heightFactor = targetHeight / height;

	if (widthFactor < heightFactor) {
		scaleFactor = widthFactor; // scale to fit height
	} else {
		scaleFactor = heightFactor; // scale to fit width
	}

	if (scaleFactor > 1.0) {
		scaleFactor = 1.0;
	}

	BOOL retina = NO;
	if (scaleFactor <= 0.5 && allowRetina) {
		scaleFactor = scaleFactor * 2;
		retina = YES;
	}

	targetWidth = round(width * scaleFactor);
	targetHeight = round(height * scaleFactor);

    CGImageRef imageRef = [self CGImage];
    CGColorSpaceRef colorSpaceInfo = CGImageGetColorSpace(imageRef);

    CGContextRef bitmap;

	bitmap = CGBitmapContextCreate(NULL, targetWidth, targetHeight, 8, 4*targetWidth, colorSpaceInfo, (CGBitmapInfo)kCGImageAlphaPremultipliedLast);

    // In the right or left cases, we need to switch scaledWidth and scaledHeight
    if (self.imageOrientation == UIImageOrientationLeft) {

        CGContextRotateCTM (bitmap, radians(90));
        CGContextTranslateCTM (bitmap, 0, -targetWidth);

    } else if (self.imageOrientation == UIImageOrientationRight) {

        CGContextRotateCTM (bitmap, radians(-90));
        CGContextTranslateCTM (bitmap, -targetHeight, 0);

    } else if (self.imageOrientation == UIImageOrientationUp) {
        // No rotation
    } else if (self.imageOrientation == UIImageOrientationDown) {
        CGContextTranslateCTM (bitmap, targetWidth, targetHeight);
        CGContextRotateCTM (bitmap, radians(-180.));
    }
	if (self.imageOrientation == UIImageOrientationUp || self.imageOrientation == UIImageOrientationDown) {
		CGContextDrawImage(bitmap, CGRectMake(0.0, 0.0, targetWidth, targetHeight), imageRef);
	} else {
		CGContextDrawImage(bitmap, CGRectMake(0.0, 0.0, targetHeight, targetWidth), imageRef);
	}
    CGImageRef ref = CGBitmapContextCreateImage(bitmap);
    UIImage* newImage = [UIImage imageWithCGImage:ref scale:(retina ? 2.0 : 1.0) orientation:UIImageOrientationUp];

    CGContextRelease(bitmap);
    CGImageRelease(ref);

    return newImage;
}

@end
