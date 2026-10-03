import asyncio
import aiohttp
import argparse
import sys


DEFAULT_TIMEOUT = 15
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_TIMEOUT = 228
HELP_TEXT = """\
hedgedcurl - хеджированный HTTP клиент.

Отправляет GET-запросы ко всем указанным URL параллельно и выводит
первый успешно полученный ответ (заголовки + тело). Остальные запросы
отменяются.

Использование:
    hedgedcurl [OPTIONS] URL [URL ...]

Опции:
    -t, --timeout SECONDS   Таймаут HTTP запроса в секундах (по умолчанию: 15)
    -h, --help              Показать эту справку и выйти
"""


def parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-t", "--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("urls", nargs="*")
    return parser.parse_args()


async def fetch(session, url):
    try:
        async with session.get(url) as response:
            body = await response.read()
            headers_text = "\n".join(f"{k}: {v}" for k, v in response.headers.items())
            version = response.version
            status_line = f"HTTP/{version.major}.{version.minor} {response.status} {response.reason}"
            text = f"{status_line}\n{headers_text}\n\n" + body.decode(errors="replace")
            return "ok", url, text
    except asyncio.CancelledError:
        raise
    except asyncio.TimeoutError:
        return "err", url, "timeout"
    except aiohttp.ClientResponseError as e:
        return "err", url, f"HTTP {e.status} {e.message}"
    except aiohttp.ClientError as e:
        return "err", url, f"client error: {e}"
    except Exception as e:
        return "err", url, f"{type(e).__name__}: {e}"


async def main(urls, timeout):
    timeout_cfg = aiohttp.ClientTimeout(total=timeout)
    errors = []

    async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        tasks = [asyncio.create_task(fetch(session, url)) for url in urls]
        pending = set(tasks)

        try:
            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    status, url, text = task.result()
                    if status == "ok":
                        print(text)
                        return EXIT_OK

                    errors.append(f"{url}: {text}")
        finally:
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)

        if errors and all(error.endswith(": timeout") for error in errors):
            print("Все запросы завершились ошибками таймаута")
            return EXIT_TIMEOUT

        print("Все запросы завершились ошибками:")
        for error in errors:
            print(error)

        return EXIT_ERROR


if __name__ == "__main__":
    try:
        args = parse_args()

        if args.help:
            print(HELP_TEXT, end="")
            sys.exit(EXIT_OK)

        if not args.urls:
            print("Ошибка: не указано ни одного URL.\n", file=sys.stderr)
            print(HELP_TEXT, end="", file=sys.stderr)
            sys.exit(EXIT_ERROR)

        if args.timeout <= 0:
            print("Ошибка: таймаут не может быть меньше 0")
            sys.exit(EXIT_ERROR)

        exit_code = asyncio.run(main(args.urls, args.timeout))
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\nПрограмма остановлена (Ctrl+C)")
        sys.exit(EXIT_ERROR)
    except Exception as e:
        print(f"Непредвиденная ошибка ({type(e).__name__}: {e})")
        sys.exit(EXIT_ERROR)
