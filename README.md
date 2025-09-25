# C++ Hello World Web Server

A minimal C++ "Hello, World!" HTTP server using the Crow framework, packaged in a small Alpine-based Docker image.

## Endpoint

- `GET /` → returns `Hello, World!` (HTTP 200)

## Run with Docker (recommended)

```bash
# Build image
docker build -t cpp-hello-server .

# Run container
docker run -p 18080:18080 cpp-hello-server

# Test
curl http://localhost:18080/
```

## Run with Docker Compose

```bash
docker-compose up --build
# then in another terminal
curl http://localhost:18080/
```

## Local build (without Docker)

Requirements: CMake, a C++17 compiler, and Boost headers (Crow dependency).

```bash
mkdir build && cd build
cmake ..
make
./server

# Test
curl http://localhost:18080/
```

## Notes

- Binds to `0.0.0.0:18080` inside the container
- Crow single-header is vendored in `include/`
- Dockerfile installs required Boost development libraries for compilation

