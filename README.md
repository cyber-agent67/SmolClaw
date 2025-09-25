# C++ Web Server

A lightweight C++ web server built with the Crow framework, containerized with Alpine Linux.

## Features

- Built with Crow C++ web framework
- Lightweight Alpine Linux container
- Multi-threaded server
- Simple REST API endpoints
- Docker and Docker Compose support

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and run the server
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### Using Docker

```bash
# Build the image
docker build -t cpp-web-server .

# Run the container
docker run -p 18080:18080 cpp-web-server
```

### Local Development

```bash
# Install dependencies (Ubuntu/Debian)
sudo apt install build-essential cmake

# Build the project
mkdir build && cd build
cmake ..
make

# Run the server
./server
```

## API Endpoints

- `GET /` - Returns "Hello, World!"

## Testing the Server

### Local Testing

1. **Start the server locally:**
   ```bash
   # Build and run
   g++ -std=c++17 -I./include -pthread -o server server.cpp
   ./server
   ```

2. **Test with curl:**
   ```bash
   # Test the root endpoint
   curl http://localhost:18080/
   
   # Expected output: "Hello, World!"
   ```

3. **Test with browser:**
   - Open your web browser
   - Navigate to `http://localhost:18080/`
   - You should see "Hello, World!" displayed

4. **Test with wget:**
   ```bash
   wget -qO- http://localhost:18080/
   ```

### Docker Testing

1. **Build and run with Docker:**
   ```bash
   # Build the image
   docker build -t cpp-web-server .
   
   # Run the container
   docker run -p 18080:18080 cpp-web-server
   ```

2. **Test the containerized server:**
   ```bash
   # Test with curl
   curl http://localhost:18080/
   
   # Test with wget
   wget -qO- http://localhost:18080/
   ```

3. **Test with Docker Compose:**
   ```bash
   # Start the service
   docker-compose up --build
   
   # In another terminal, test the server
   curl http://localhost:18080/
   ```

### Health Check

You can also create a simple health check script:

```bash
#!/bin/bash
# health_check.sh
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:18080/)
if [ $response -eq 200 ]; then
    echo "✅ Server is healthy (HTTP $response)"
    echo "Response: $(curl -s http://localhost:18080/)"
else
    echo "❌ Server is not responding (HTTP $response)"
    exit 1
fi
```

### Troubleshooting

- **Port already in use**: Change the port in `server.cpp` or kill the process using port 18080
- **Permission denied**: Make sure the server binary has execute permissions (`chmod +x server`)
- **Connection refused**: Ensure the server is running and listening on the correct port

## Configuration

- **Port**: 18080 (configurable in server.cpp)
- **Threads**: 2 (default Crow configuration)

## Docker Image

The Docker image is based on Alpine Linux for minimal size and security.

## Development

The project uses CMake for building. The Crow framework is included as a single header file in the `include/` directory.

## License

MIT License
