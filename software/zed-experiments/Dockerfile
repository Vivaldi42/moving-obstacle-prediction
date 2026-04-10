FROM stereolabs/zed:5.2.2-gl-devel-cuda12.8-ubuntu24.04

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libopencv-dev \
        python3 \
        python3-venv \
        python3-pip && \
    rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv ${VIRTUAL_ENV} && \
    ${VIRTUAL_ENV}/bin/pip install --no-cache-dir "numpy<2" opencv-python requests open3d
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN if [ -f /usr/local/zed/get_python_api.py ]; then \
        ${VIRTUAL_ENV}/bin/python /usr/local/zed/get_python_api.py; \
    fi

ENV ZED_SDK_ROOT=/usr/local/zed
ENV LD_LIBRARY_PATH=/usr/local/zed/lib
ENV PYTHONPATH=/usr/local/zed/python

COPY CMakeLists.txt /app/CMakeLists.txt
COPY src /app/src

RUN mkdir -p /app/build && cd /app/build && \
    cmake -DCMAKE_LIBRARY_PATH=/usr/local/cuda/lib64/stubs \
          -DCMAKE_CXX_FLAGS="-Wl,--allow-shlib-undefined" .. && \
    make -j"$(nproc)"

CMD ["/app/build/zed_algo_sandbox"]
