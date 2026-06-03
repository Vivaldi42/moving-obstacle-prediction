# calc_ball_3d_position — data flow

## Input

The xyz_map is a `(H, W, 3)` array. Each pixel `(u, v)` stores a 3D point already in metres:

```
xyz_map[v, u] = [X, Y, Z]
```

The ZED computed these values internally via stereo disparity.

---

## Step 1 - bbox centre

```
cx = (x1 + x2) / 2
cy = (y1 + y2) / 2
```

Image-space centroid of the YOLO bbox, in pixels.

---

## Step 2 - patch extraction

```
u ∈ [cx - 4, cx + 4]
v ∈ [cy - 4, cy + 4]
```

A 9×9 = 81 pixel neighbourhood around the bbox centre. Each pixel contributes one 3D point:

```
P = { xyz_map[v, u] | u ∈ [cx±4], v ∈ [cy±4] }
```

---

## Step 3 - filter invalids

```
P_valid = { (X, Y, Z) ∈ P | X, Y, Z are all finite }
```

Drops pixels the ZED could not measure (stored as nan or inf).

---

## Step 4 - median

```
X_out = median({ X | (X,Y,Z) ∈ P_valid })
Y_out = median({ Y | (X,Y,Z) ∈ P_valid })
Z_out = median({ Z | (X,Y,Z) ∈ P_valid })
```

Each axis is independent. The median is robust to the few outlier pixels that stereo depth gets wrong.

---

## Output

```
(X_out, Y_out, Z_out)  — metres, camera frame
```

- **X_out, Y_out** - 3D position of the ball's geometric centre laterally, because the patch is centred on the bbox centre which aligns with the ball's centre in image space.
- **Z_out** - depth to the front surface of the ball, because the centre pixels of the bbox face the camera directly.

---

## Manual measurement reference

When filling in ground truth values:

| Axis | Measure to |
|------|-----------|
| Z | front surface of the ball (tape from camera lens to ball) |
| X | ball geometric centre, horizontal offset from camera optical axis (right = positive) |
| Y | ball geometric centre, vertical offset from camera optical axis (down = positive) |
