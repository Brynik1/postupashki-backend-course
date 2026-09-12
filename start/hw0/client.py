import socket


CONNECT_TIMEOUT = 5.0   # на установку соединения
READ_TIMEOUT = 5.0      # на чтение


def recv_until_eof(sock, bufsize=1024):
    chunks = []
    while True:
        chunk = sock.recv(bufsize)
        if not chunk:  # сервер закрыл соединение
            return b"".join(chunks)

        chunks.append(chunk)


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(CONNECT_TIMEOUT)  # Таймаут и на connect, и на последующие recv
    server_address = ('localhost', 8080)

    try:
        client_socket.connect(server_address)

        client_socket.settimeout(READ_TIMEOUT)  # Таймаут для чтения
        response = recv_until_eof(client_socket)  # Читает данные из сокета до закрытия соединения (EOF)

        if response == b"OK\n":
            print("Получен ожидаемый ответ 'OK\\n'")
        else:
            print(f"Получен неожиданный ответ '{response}'")

    except ConnectionRefusedError:
        print(f"Ошибка: не удалось подключиться к {server_address[0]}:{server_address[1]}")
    except socket.timeout:
        print(f"Ошибка: превышен таймаут подключения/чтения")
    except OSError as e:
        print(f"Ошибка сокета: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
    finally:
        client_socket.close()
        print("Соединение закрыто")


if __name__ == "__main__":
    main()