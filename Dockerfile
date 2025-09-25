# Use Alpine Linux as base image
FROM alpine:latest

# Install build dependencies
RUN apk add --no-cache \
    g++ \
    cmake \
    make \
    linux-headers \
    musl-dev \
    boost-dev \
    boost-static

# Set working directory
WORKDIR /app

# Copy source files
COPY server.cpp .
COPY include/ include/
COPY CMakeLists.txt .

# Create build directory and build the application
RUN mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    cp server /app/server

# Remove build dependencies to reduce image size
RUN apk del g++ cmake make linux-headers musl-dev

# Expose port
EXPOSE 18080

# Run the server
CMD ["./server"]

