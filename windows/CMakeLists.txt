cmake_minimum_required(VERSION 3.24)
project(IsoFlickerWin LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(IsoFlickerWin
    src/main.cpp
    src/swap_chain.cpp
    src/audio_engine.cpp
    src/telemetry.cpp
)

target_include_directories(IsoFlickerWin PRIVATE include)

target_link_libraries(IsoFlickerWin PRIVATE
    d3d11
    dxgi
    dxguid
    ole32
    mmdevapi
    avrt
)

add_compile_definitions(ISOFLICKER_VERSION="0.1.0")
