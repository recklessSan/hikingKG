from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update

from bot.config import load_settings
from bot.demo import run_demo
from bot.parsers.chat1 import parse_chat1
from bot.parsers.chat2 import parse_chat2
from bot.parsers.chat3 import parse_chat3
from bot.parsers.phones import format_phone
from bot.parsers.redact import redact_card_numbers


def _setup_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        return


def _start_health_server(port: int) -> None:
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()


def _print_parse_result(result) -> None:
    if not result.batches:
        print(f"ничего не разобрано ({result.skipped_reason})")
        return
    for batch in result.batches:
        print(
            f"{batch.event_type}: {batch.bank} {batch.card_count} шт"
            f"{' кэш' if batch.is_cash else ''}"
            f"{' без ЛК' if batch.without_lk else ''}"
            f"{' ' + batch.batch_ref if batch.batch_ref else ''}"
        )
        if batch.phones:
            print("  телефоны: " + ", ".join(format_phone(item.e164) for item in batch.phones))
        if batch.excerpt:
            print(f"  excerpt: {redact_card_numbers(batch.excerpt)}")


def cmd_parse(args: argparse.Namespace) -> int:
    text = args.text
    if args.file:
        text = open(args.file, encoding="utf-8").read()
    if not text:
        print("передай --text или --file")
        return 1
    if args.chat == "1":
        result = parse_chat1(text)
    elif args.chat == "2":
        result = parse_chat2(text)
    else:
        result = parse_chat3(text, mode=args.mode)
    _print_parse_result(result)
    return 0


def cmd_run() -> int:
    settings = load_settings()
    from bot.app import build_application

    application = build_application(settings)
    allowed = Update.ALL_TYPES
    if settings.webhook_url:
        port = int(os.environ.get("PORT", settings.port))
        url_path = settings.webhook_path.strip("/")
        webhook_url = f"{settings.webhook_url}/{url_path}"
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=url_path,
            webhook_url=webhook_url,
            allowed_updates=allowed,
        )
        return 0

    port_env = os.environ.get("PORT")
    if port_env:
        _start_health_server(int(port_env))
    application.run_polling(allowed_updates=allowed, drop_pending_updates=True)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Card analytics telegram bot")
    sub = parser.add_subparsers(dest="command")

    parse_cmd = sub.add_parser("parse", help="разобрать текст без Telegram")
    parse_cmd.add_argument("--chat", choices=["1", "2", "3"], default="1")
    parse_cmd.add_argument("--mode", default="auto", help="режим чата 3: auto|chat1|chat2")
    parse_cmd.add_argument("--text", default="")
    parse_cmd.add_argument("--file")

    sub.add_parser("demo", help="локальная проверка парсеров и отчёта")
    sub.add_parser("run", help="запустить бота")
    return parser


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "run"
    if command == "parse":
        return cmd_parse(args)
    if command == "demo":
        return asyncio.run(run_demo())
    if command == "run":
        return cmd_run()
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
