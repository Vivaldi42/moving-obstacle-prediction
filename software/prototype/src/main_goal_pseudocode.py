from pipeline import open_svo

# --- New design

# open SVO2 via frame provider (swappable with OpenCV stereo later)
# initialise YOLO, Kalman filter, metrics accumulators

# for each frame:
#   get (left_rgb, xyz_map, conf_map) from frame provider
#   detect object in left_rgb with YOLO → centre pixel (cx, cy)
#   skip frame if no detection or conf_map[cy, cx] unreliable
#   observe (x, y, z) = xyz_map[cy, cx]
#   update Kalman filter → predict next 6 positions (0.2 s horizon)
#   record ADE, FDE, TC, latency against ground truth

# report metrics

# --- Old design


# open the SVO2 file

# get camera intrinsics (needed later for pixel -> 3D conversion)

# loop over every frame:

    # grab RGB image
    # grab depth map
    # grab timestamp

    # run YOLO on RGB -> get bounding box of the ball (or skip frame if not detected)

    # get centre pixel of bounding box
    # look up depth at that pixel
    # convert pixel + depth -> (x, y, z) in metres

    # feed (x, y, z) into Kalman filter -> get filtered position + velocity

    # print or log the result

# close the camera
