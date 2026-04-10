cmake_minimum_required(VERSION 3.16)
project(zed_algo_sandbox CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ZED 5 REQUIRED)
find_package(CUDA REQUIRED)
find_package(OpenCV REQUIRED COMPONENTS core highgui imgproc)

add_executable(zed_algo_sandbox src/main.cpp)
target_link_libraries(zed_algo_sandbox ${ZED_LIBRARIES} ${CUDA_CUDA_LIBRARY} ${OpenCV_LIBS} pthread)
target_include_directories(zed_algo_sandbox PRIVATE ${ZED_INCLUDE_DIRS} ${CUDA_INCLUDE_DIRS})
