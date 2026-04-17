#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <sl/Camera.hpp>

#include <chrono>
#include <iomanip>
#include <iostream>
#include <sstream>
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

std::string fpsText(double fps) {
    std::ostringstream stream;
    stream << std::fixed << std::setprecision(1) << "FPS: " << fps;
    return stream.str();
}

}  // namespace

int main() {
    sl::Camera zed;

    sl::InitParameters init_params;
    init_params.camera_resolution = sl::RESOLUTION::HD720;
    init_params.depth_mode = sl::DEPTH_MODE::NONE;
    init_params.coordinate_units = sl::UNIT::METER;

    const auto open_error = zed.open(init_params);
    if (open_error != sl::ERROR_CODE::SUCCESS) {
        std::cerr << "zed.open failed: " << sl::toString(open_error) << std::endl;
        return 1;
    }

    sl::RuntimeParameters runtime_params;
    sl::Mat left_image;

    cv::namedWindow("3dpipe", cv::WINDOW_AUTOSIZE);
    std::cout << "Streaming left ZED image. Press q or Esc to quit." << std::endl;

    auto last_frame_time = std::chrono::steady_clock::now();
    auto last_fps_print_time = last_frame_time;
    double fps = 0.0;

    while (true) {
        const auto grab_error = zed.grab(runtime_params);
        if (grab_error != sl::ERROR_CODE::SUCCESS) {
            if (grab_error != sl::ERROR_CODE::CAMERA_REBOOTING) {
                std::cerr << "zed.grab failed: " << sl::toString(grab_error) << std::endl;
            }
            continue;
        }

        zed.retrieveImage(left_image, sl::VIEW::LEFT, sl::MEM::CPU);

        cv::Mat frame = slMatToCvMat(left_image).clone();
        cv::cvtColor(frame, frame, cv::COLOR_BGRA2BGR);

        const auto now = std::chrono::steady_clock::now();
        const double seconds = std::chrono::duration<double>(now - last_frame_time).count();
        if (seconds > 0.0) {
            fps = 1.0 / seconds;
        }
        last_frame_time = now;

        if (std::chrono::duration<double>(now - last_fps_print_time).count() >= 2.0) {
            std::cout << fpsText(fps) << std::endl;
            last_fps_print_time = now;
        }

        cv::putText(
            frame,
            fpsText(fps),
            cv::Point(20, 40),
            cv::FONT_HERSHEY_SIMPLEX,
            1.0,
            cv::Scalar(0, 255, 0),
            2);

        cv::imshow("3dpipe", frame);
        const int key = cv::waitKey(1);
        if (key == 'q' || key == 27) {
            break;
        }
    }

    cv::destroyAllWindows();
    zed.close();
    return 0;
}
