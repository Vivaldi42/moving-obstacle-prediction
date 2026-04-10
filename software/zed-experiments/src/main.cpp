#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <sl/Camera.hpp>

#include <cmath>
#include <iostream>
#include <limits>
#include <string>

namespace {

cv::Mat slMatToCvMat(sl::Mat& image) {
    return cv::Mat(
        static_cast<int>(image.getHeight()),
        static_cast<int>(image.getWidth()),
        CV_8UC4,
        image.getPtr<sl::uchar1>(sl::MEM::CPU),
        image.getStepBytes(sl::MEM::CPU));
}

float depthAtCenter(sl::Mat& depth) {
    const int x = static_cast<int>(depth.getWidth() / 2);
    const int y = static_cast<int>(depth.getHeight() / 2);
    float depth_value = 0.0f;
    const auto err = depth.getValue(x, y, &depth_value);
    if (err != sl::ERROR_CODE::SUCCESS || !std::isfinite(depth_value)) {
        return std::numeric_limits<float>::quiet_NaN();
    }
    return depth_value;
}

void runAlgorithm(sl::Mat& left_image, sl::Mat& depth, cv::Mat& frame) {
    const float center_depth = depthAtCenter(depth);
    std::string text = "Depth center: N/A";
    if (std::isfinite(center_depth)) {
        text = "Depth center: " + std::to_string(center_depth) + " m";
    }

    cv::putText(
        frame,
        text,
        cv::Point(20, 35),
        cv::FONT_HERSHEY_SIMPLEX,
        0.8,
        cv::Scalar(255, 255, 255),
        2);

    (void)left_image;
}

}  // namespace

int main() {
    sl::Camera zed;

    sl::InitParameters init_params;
    init_params.camera_resolution = sl::RESOLUTION::HD720;
    init_params.depth_mode = sl::DEPTH_MODE::ULTRA;
    init_params.coordinate_units = sl::UNIT::METER;

    auto err = zed.open(init_params);
    if (err != sl::ERROR_CODE::SUCCESS) {
        std::cerr << "zed.open failed: " << sl::toString(err) << std::endl;
        return 1;
    }

    sl::RuntimeParameters runtime;
    sl::Mat left_image;
    sl::Mat depth;

    cv::namedWindow("ZED Algo Sandbox", cv::WINDOW_AUTOSIZE);
    std::cout << "Running ZED sandbox. Press q in the window to stop." << std::endl;

    while (true) {
        err = zed.grab(runtime);
        if (err != sl::ERROR_CODE::SUCCESS) {
            if (err != sl::ERROR_CODE::CAMERA_REBOOTING) {
                std::cerr << "zed.grab failed: " << sl::toString(err) << std::endl;
            }
            continue;
        }

        zed.retrieveImage(left_image, sl::VIEW::LEFT, sl::MEM::CPU);
        zed.retrieveMeasure(depth, sl::MEASURE::DEPTH, sl::MEM::CPU);

        cv::Mat frame = slMatToCvMat(left_image).clone();
        cv::cvtColor(frame, frame, cv::COLOR_BGRA2BGR);

        runAlgorithm(left_image, depth, frame);

        cv::imshow("ZED Algo Sandbox", frame);
        const int key = cv::waitKey(1);
        if (key == 'q' || key == 27) {
            break;
        }
    }

    cv::destroyAllWindows();
    zed.close();
    return 0;
}
