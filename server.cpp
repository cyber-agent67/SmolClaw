#include "crow_all.h"
#include <string>

int main() {
    crow::SimpleApp app;

    CROW_ROUTE(app, "/").methods(crow::HTTPMethod::GET)([] {
        return crow::response(200, "Hello, World!\n");
    });

    std::cout << "Server listening on http://0.0.0.0:18080" << std::endl;
    app.port(18080).bindaddr("0.0.0.0").run();
    return 0;
}
