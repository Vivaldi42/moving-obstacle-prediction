# Image Processor/Image Signal Processor (ISP)

**Overview:**  
An ISP is a system that converts raw data from an image sensor into a visually meaningful digital image.

![Before/After ISP](before_after_isp.jpg)

**Core idea:**  
An ISP processes raw pixel data captured by a camera sensor, which is typically noisy and incomplete. It applies a sequence of algorithms such as demosaicing to reconstruct full-color images from Bayer patterns, and noise reduction to improve image clarity. The ISP also adjusts image properties like white balance, exposure, and color correction to ensure accurate representation. Additional steps like sharpening and HDR processing may be included to enhance visual quality. Overall, it transforms low-level sensor data into a refined image suitable for human viewing or further processing.

**Input:**  
Raw image data from an image sensor (e.g., Bayer-pattern pixel data).

**Output:**  
Processed digital image (e.g., RGB image ready for display or storage).

**Depends on:**  
Image sensor hardware, lens system, analog-to-digital converter (ADC), and embedded processing algorithms.

**Used in:**  
Smartphones, digital cameras, webcams, surveillance systems, and embedded vision systems.

---
# Raw image data

**Overview:**  
Raw image data is the unprocessed pixel information directly captured by an image sensor.

![Bayer image](bayer_image.png)

**Core idea:**  
Raw image data consists of the direct measurements of light intensity recorded at each sensor pixel before any processing is applied. In most cameras, this data follows a Bayer pattern, where each pixel captures only one color component (red, green, or blue). The data is typically high bit-depth and contains noise, sensor imperfections, and no color interpolation. It has not undergone corrections such as white balance, demosaicing, or compression. Because of this, raw data preserves maximum detail and dynamic range, making it suitable for high-quality image processing.

**Input:**  
Light signals captured by the image sensor and converted into electrical signals.

**Output:**  
Digitized but unprocessed pixel values (raw sensor data).

**Depends on:**  
Image sensor design, color filter array (e.g., Bayer filter), analog-to-digital conversion, and sensor calibration.

**Used in:**  
Digital cameras, smartphone cameras, professional photography workflows, and computer vision preprocessing pipelines.

---

  
**Demosaicing:** Converting the raw sensor data from a color filter array (such as Bayer filter) into a full-color image.  
  
**Noise reduction:** Filtering out noise and artifacts from the sensor data to improve image quality.  
  
**Color correction:** Adjusting color balance and correcting color distortions to achieve accurate color reproduction.  
  
**White balance:** Adjusting the overall color temperature of the image to match lighting conditions.  
  
**Sharpness enhancement:** Applying algorithms to enhance image sharpness and detail.  
  
**Exposure control:** Adjusting exposure parameters such as brightness and contrast to optimize image visibility.  
  
Image signal processors play a crucial role in digital imaging devices by processing sensor data in real-time or near real-time, enabling fast capture and high-quality output of images and videos. They are essential components in modern digital cameras, smartphones, surveillance cameras, and other imaging devices.



rtp protocol

- [Accelerometer](https://www.stereolabs.com/docs/sensors/imu/)
- [Gyroscope](https://www.stereolabs.com/docs/sensors/imu/)
- [Barometer](https://www.stereolabs.com/docs/sensors/barometer/)
- [Magnetometer](https://www.stereolabs.com/docs/sensors/magnetometer/)
- [Temperature sensors](https://www.stereolabs.com/docs/sensors/temperature/)

6dof translation (X, Y, Z) and rotation (roll, pitch, yaw).



svo2 file format
H.264
H.265
lossless compression
hardware-based encoder (referred to as NVENC in GPU)
bitrate

---
image signal processor
brightness
contrast
hue
color intensity
saturation
sharpness
gamma
white balance
gain
(auto)exposure
shutter speed
noise
motion blur
exposure range
analog gain range
digital gain range
denoising
exp. compensation
scene luminance

---

hw protocols
usb3
gmsl2


---
tailscale

---
---
---

[Algorithm] Kalman Filter

Purpose:
Estimate state under noise

Core idea:
Recursive Bayesian update (Gaussian)

Used in:
- SLAM
- Tracking

Depends on:
- Probability
- Linear algebra

input

output


# Resources

https://www.photonics.com/Dictionary/image-signal-processor/d8661

https://www.thine.co.jp/en/contents/detail/cdk-background.html

https://en.wikipedia.org/wiki/Bayer_filter