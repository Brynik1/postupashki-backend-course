import socket
import threading


def handle_client(client_socket, client_address):
    try:
        client_socket.sendall(b"OK\n")
    except OSError as e:
        print(f"Ошибка при работе с {client_address}: {e}")
    finally:
        client_socket.close()
        print(f"Соединение с {client_address} закрыто")


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 8080)

    try:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(server_address)
        server_socket.listen(128)
        print(f"Сервер запущен на {server_address[0]}:{server_address[1]}")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Подключен клиент: {client_address}")

            t = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True,
            )
            t.start()

    except OSError as e:
        print(f"Ошибка сокета: {e}")
    except KeyboardInterrupt:
        print("\nСервер остановлен (Ctrl+C)")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
    finally:
        server_socket.close()
        print("Сервер завершил работу")


if __name__ == "__main__":
    main()