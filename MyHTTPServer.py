import os
import socket

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
WEB_ROOT = "htdocs"


def build_response(status_code, body, content_type="text/html; charset=utf-8"):
    status_messages = {
        200: "OK",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Internal Server Error",
    }

    reason = status_messages.get(status_code, "OK")
    body_bytes = body.encode("utf-8")

    response_headers = [
        f"HTTP/1.1 {status_code} {reason}",
        f"Content-Type: {content_type}",
        f"Content-Length: {len(body_bytes)}",
        "Connection: close",
        "",
        "",
    ]
    header_bytes = "\r\n".join(response_headers).encode("utf-8")
    return header_bytes + body_bytes


def guess_content_type(filename):
    if filename.endswith(".html"):
        return "text/html; charset=utf-8"
    if filename.endswith(".css"):
        return "text/css; charset=utf-8"
    if filename.endswith(".js"):
        return "application/javascript; charset=utf-8"
    if filename.endswith(".png"):
        return "image/png"
    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
        return "image/jpeg"
    return "text/plain; charset=utf-8"


def safe_join(root, request_path):
    request_path = request_path.split("?", 1)[0]
    request_path = request_path.split("#", 1)[0]

    if request_path == "/":
        request_path = "/index.html"

    normalized = os.path.normpath(request_path.lstrip("/"))
    full_path = os.path.abspath(os.path.join(root, normalized))
    root_abs = os.path.abspath(root)

    if not full_path.startswith(root_abs):
        return None

    return full_path


def handle_client(connection_socket):
    try:
        request_data = connection_socket.recv(4096).decode("utf-8", errors="ignore")
        if not request_data:
            return

        print("----- Request Start -----")
        print(request_data)
        print("------ Request End ------")

        request_line = request_data.splitlines()[0]
        parts = request_line.split()

        if len(parts) < 3:
            response = build_response(
                500,
                "<h1>500 Internal Server Error</h1><p>Malformed request line.</p>"
            )
            connection_socket.sendall(response)
            return

        method, path, version = parts

        if method != "GET":
            body = """
            <html>
            <head><title>405 Method Not Allowed</title></head>
            <body style="font-family: Arial; padding: 40px;">
                <h1>405 Method Not Allowed</h1>
                <p>This simple server only supports GET requests.</p>
            </body>
            </html>
            """
            response = build_response(405, body)
            connection_socket.sendall(response)
            return

        file_path = safe_join(WEB_ROOT, path)

        if file_path is None or not os.path.exists(file_path) or not os.path.isfile(file_path):
            body = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>404 Not Found</title>
                <style>
                    body {{
                        margin: 0;
                        min-height: 100vh;
                        display: grid;
                        place-items: center;
                        font-family: Arial, sans-serif;
                        background: linear-gradient(135deg, #111827, #1f2937, #374151);
                        color: white;
                    }}
                    .box {{
                        max-width: 700px;
                        padding: 40px;
                        border-radius: 24px;
                        background: rgba(255,255,255,0.08);
                        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                        text-align: center;
                    }}
                    a {{
                        color: #67e8f9;
                    }}
                </style>
            </head>
            <body>
                <div class="box">
                    <h1>404 Not Found</h1>
                    <p>The requested path <code>{path}</code> does not exist.</p>
                    <p><a href="/index.html">Return to homepage</a></p>
                </div>
            </body>
            </html>
            """
            response = build_response(404, body)
            connection_socket.sendall(response)
            return

        content_type = guess_content_type(file_path)

        if content_type.startswith("image/"):
            with open(file_path, "rb") as fin:
                body_bytes = fin.read()
            headers = [
                "HTTP/1.1 200 OK",
                f"Content-Type: {content_type}",
                f"Content-Length: {len(body_bytes)}",
                "Connection: close",
                "",
                "",
            ]
            connection_socket.sendall("\r\n".join(headers).encode("utf-8") + body_bytes)
        else:
            with open(file_path, "r", encoding="utf-8") as fin:
                content = fin.read()
            response = build_response(200, content, content_type)
            connection_socket.sendall(response)

    except Exception as e:
        print("Server error:", e)
        body = f"""
        <html>
        <head><title>500 Internal Server Error</title></head>
        <body style="font-family: Arial; padding: 40px;">
            <h1>500 Internal Server Error</h1>
            <p>{str(e)}</p>
        </body>
        </html>
        """
        response = build_response(500, body)
        try:
            connection_socket.sendall(response)
        except Exception:
            pass
    finally:
        connection_socket.close()


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)

    print(f"Server is running at http://{SERVER_HOST}:{SERVER_PORT}/")

    try:
        while True:
            connection_socket, addr = server_socket.accept()
            print(f"Connection from {addr}")
            handle_client(connection_socket)
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()