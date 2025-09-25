cmake_minimum_required(VERSION 3.10)
project(cpp_web_server)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(Threads REQUIRED)
find_package(Boost REQUIRED COMPONENTS system)

# Include directories
include_directories(include)

# Add executable
add_executable(server server.cpp)

# Link libraries
target_link_libraries(server Threads::Threads Boost::system)

# Compiler flags
target_compile_options(server PRIVATE -Wall -Wextra -O2)

