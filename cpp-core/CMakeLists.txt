cmake_minimum_required(VERSION 3.20)
project(secagent_core VERSION 0.3.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(MSVC)
    add_compile_options(/W4 /O2)
else()
    add_compile_options(-Wall -Wextra -O3)
endif()

include_directories(include)

file(GLOB_RECURSE SOURCES "src/*.cpp")
list(REMOVE_ITEM SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/src/main.cpp")

# Shared C++ core library
add_library(secagent_core SHARED ${SOURCES})

# Standalone executable
add_executable(secagent_core_bin src/main.cpp)
target_link_libraries(secagent_core_bin PRIVATE secagent_core)

if(WIN32)
    target_link_libraries(secagent_core PRIVATE ws2_32)
    target_link_libraries(secagent_core_bin PRIVATE ws2_32)
endif()
