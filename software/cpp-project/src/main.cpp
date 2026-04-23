#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <sl/Camera.hpp>

#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
#include <vector>

namespace {

constexpr double kBackgroundLearningRate = 0.01;
constexpr int kMotionThreshold = 25;
constexpr int kMinContourAreaPixels = 1200;
constexpr float kMinDepthMeters = 0.2f;
constexpr float kMaxDepthMeters = 10.0f;
constexpr int kPointSampleStride = 3;

struct DetectionResult {
    bool found = false;
    cv::Rect bbox;
    cv::Point2f image_centroid;
    cv::Point3f position_m;
    float median_depth_m = std::numeric_limits<float>::quiet_NaN();
    int mask_pixels = 0;
};

cv::Mat slMatToCvMat(sl::Mat& image, int cv_type) {
    return cv::Mat(
        static_cast<int>(image.getHeight()),
        static_cast<int>(image.getWidth()),
        cv_type,
        image.getPtr<sl::uchar1>(sl::MEM::CPU),
        image.getStepBytes(sl::MEM::CPU));
}

bool isFiniteDepth(float depth_m) {
    return std::isfinite(depth_m) && depth_m >= kMinDepthMeters && depth_m <= kMaxDepthMeters;
}

float median(std::vector<float>& values) {
    const auto mid = values.begin() + static_cast<std::ptrdiff_t>(values.size() / 2);
    std::nth_element(values.begin(), mid, values.end());
    return *mid;
}

DetectionResult detectSingleMovingObject(
    const cv::Mat& bgr_frame,
    const cv::Mat& depth_map,
    const cv::Mat& point_cloud,
    cv::Mat& background_gray_f32,
    cv::Mat& debug_mask) {
    DetectionResult result;

    cv::Mat gray_frame;
    cv::cvtColor(bgr_frame, gray_frame, cv::COLOR_BGR2GRAY);
    cv::GaussianBlur(gray_frame, gray_frame, cv::Size(7, 7), 0.0);

    if (background_gray_f32.empty()) {
        gray_frame.convertTo(background_gray_f32, CV_32F);
        debug_mask = cv::Mat::zeros(gray_frame.size(), CV_8UC1);
        return result;
    }

    cv::accumulateWeighted(gray_frame, background_gray_f32, kBackgroundLearningRate);

    cv::Mat background_gray_u8;
    background_gray_f32.convertTo(background_gray_u8, CV_8U);

    cv::Mat motion_mask;
    cv::absdiff(gray_frame, background_gray_u8, motion_mask);
    cv::threshold(motion_mask, motion_mask, kMotionThreshold, 255, cv::THRESH_BINARY);

    cv::Mat depth_valid_mask = cv::Mat::zeros(depth_map.size(), CV_8UC1);
    for (int y = 0; y < depth_map.rows; ++y) {
        const float* depth_row = depth_map.ptr<float>(y);
        uchar* mask_row = depth_valid_mask.ptr<uchar>(y);
        for (int x = 0; x < depth_map.cols; ++x) {
            mask_row[x] = isFiniteDepth(depth_row[x]) ? 255 : 0;
        }
    }

    cv::bitwise_and(motion_mask, depth_valid_mask, debug_mask);
    cv::morphologyEx(
        debug_mask,
        debug_mask,
        cv::MORPH_OPEN,
        cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(5, 5)));
    cv::morphologyEx(
        debug_mask,
        debug_mask,
        cv::MORPH_CLOSE,
        cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(11, 11)));
    cv::dilate(
        debug_mask,
        debug_mask,
        cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(7, 7)));

    std::vector<std::vector<cv::Point>> contours;
    cv::findContours(debug_mask.clone(), contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);

    double best_area = 0.0;
    std::vector<cv::Point> best_contour;
    for (const auto& contour : contours) {
        const double area = cv::contourArea(contour);
        if (area < kMinContourAreaPixels || area <= best_area) {
            continue;
        }
        best_area = area;
        best_contour = contour;
    }

    if (best_contour.empty()) {
        return result;
    }

    result.bbox = cv::boundingRect(best_contour);

    cv::Mat contour_mask = cv::Mat::zeros(debug_mask.size(), CV_8UC1);
    cv::drawContours(contour_mask, std::vector<std::vector<cv::Point>>{best_contour}, -1, cv::Scalar(255), cv::FILLED);
    cv::bitwise_and(debug_mask, contour_mask, contour_mask);
    result.mask_pixels = cv::countNonZero(contour_mask);
    if (result.mask_pixels == 0) {
        return result;
    }

    const cv::Moments moments = cv::moments(contour_mask, true);
    if (moments.m00 <= 0.0) {
        return result;
    }

    result.image_centroid = cv::Point2f(
        static_cast<float>(moments.m10 / moments.m00),
        static_cast<float>(moments.m01 / moments.m00));

    std::vector<float> xs;
    std::vector<float> ys;
    std::vector<float> zs;
    xs.reserve(result.mask_pixels / (kPointSampleStride * kPointSampleStride) + 1);
    ys.reserve(xs.capacity());
    zs.reserve(xs.capacity());

    const int y_end = std::min(result.bbox.y + result.bbox.height, point_cloud.rows);
    const int x_end = std::min(result.bbox.x + result.bbox.width, point_cloud.cols);
    for (int y = std::max(result.bbox.y, 0); y < y_end; y += kPointSampleStride) {
        const auto* mask_row = contour_mask.ptr<uchar>(y);
        const auto* point_row = point_cloud.ptr<cv::Vec4f>(y);
        for (int x = std::max(result.bbox.x, 0); x < x_end; x += kPointSampleStride) {
            if (mask_row[x] == 0) {
                continue;
            }

            const cv::Vec4f& point = point_row[x];
            const float depth_m = point[2];
            if (!isFiniteDepth(depth_m) || !std::isfinite(point[0]) || !std::isfinite(point[1])) {
                continue;
            }

            xs.push_back(point[0]);
            ys.push_back(point[1]);
            zs.push_back(point[2]);
        }
    }

    if (zs.empty()) {
        return result;
    }

    result.position_m = cv::Point3f(median(xs), median(ys), median(zs));
    result.median_depth_m = result.position_m.z;
    result.found = true;
    debug_mask = contour_mask;
    return result;
}

}  // namespace

int main() {
    sl::Camera zed;

    sl::InitParameters init_params;
    init_params.camera_resolution = sl::RESOLUTION::HD720;
    init_params.depth_mode = sl::DEPTH_MODE::ULTRA;
    init_params.coordinate_units = sl::UNIT::METER;

    const auto open_error = zed.open(init_params);
    if (open_error != sl::ERROR_CODE::SUCCESS) {
        std::cerr << "zed.open failed: " << sl::toString(open_error) << std::endl;
        return 1;
    }

    sl::RuntimeParameters runtime_params;
    runtime_params.enable_fill_mode = true;

    sl::Mat left_image;
    sl::Mat depth_map;
    sl::Mat point_cloud;

    cv::namedWindow("3dpipe", cv::WINDOW_AUTOSIZE);
    cv::namedWindow("motion_mask", cv::WINDOW_AUTOSIZE);
    std::cout
        << "Streaming ZED RGB-D with single moving object detection. Press q or Esc to quit."
        << std::endl;

    cv::Mat background_gray_f32;
    cv::Mat motion_mask;

    while (true) {
        const auto grab_error = zed.grab(runtime_params);
        if (grab_error != sl::ERROR_CODE::SUCCESS) {
            if (grab_error != sl::ERROR_CODE::CAMERA_REBOOTING) {
                std::cerr << "zed.grab failed: " << sl::toString(grab_error) << std::endl;
            }
            continue;
        }

        zed.retrieveImage(left_image, sl::VIEW::LEFT, sl::MEM::CPU);
        zed.retrieveMeasure(depth_map, sl::MEASURE::DEPTH, sl::MEM::CPU);
        zed.retrieveMeasure(point_cloud, sl::MEASURE::XYZRGBA, sl::MEM::CPU);

        cv::Mat frame = slMatToCvMat(left_image, CV_8UC4).clone();
        cv::cvtColor(frame, frame, cv::COLOR_BGRA2BGR);

        cv::Mat depth = slMatToCvMat(depth_map, CV_32FC1);
        cv::Mat xyzrgba = slMatToCvMat(point_cloud, CV_32FC4);

        const DetectionResult detection =
            detectSingleMovingObject(frame, depth, xyzrgba, background_gray_f32, motion_mask);

        if (detection.found) {
            cv::rectangle(frame, detection.bbox, cv::Scalar(0, 255, 255), 2);
            cv::circle(frame, detection.image_centroid, 6, cv::Scalar(0, 0, 255), cv::FILLED);
            std::cout << "\rObject xyz(m): "
                      << detection.position_m.x << ", "
                      << detection.position_m.y << ", "
                      << detection.position_m.z << "   " << std::flush;
        } else {
            std::cout << "\rObject xyz(m): none           " << std::flush;
        }

        cv::imshow("3dpipe", frame);
        cv::imshow("motion_mask", motion_mask);

        const int key = cv::waitKey(1);
        if (key == 'q' || key == 27) {
            break;
        }
    }

    cv::destroyAllWindows();
    zed.close();
    return 0;
}
