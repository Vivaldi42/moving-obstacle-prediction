cmake_minimum_required(VERSION 3.16)
project(3dpipe CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(POLICY CMP0146)
  cmake_policy(SET CMP0146 OLD)
endif()

if(POLICY CMP0153)
  cmake_policy(SET CMP0153 OLD)
endif()

find_package(ZED 5 REQUIRED)
find_package(CUDA REQUIRED)
find_package(OpenCV REQUIRED COMPONENTS core highgui imgproc)

add_executable(3dpipe src/main.cpp)
target_link_libraries(3dpipe ${ZED_LIBRARIES} ${CUDA_CUDA_LIBRARY} ${OpenCV_LIBS} pthread)
target_include_directories(3dpipe PRIVATE ${ZED_INCLUDE_DIRS} ${CUDA_INCLUDE_DIRS})
