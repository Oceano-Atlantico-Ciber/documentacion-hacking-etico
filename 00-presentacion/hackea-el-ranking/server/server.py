"""Server for the "Hack the Leaderboard" game.

The MODE environment variable selects one of two modes:
  trusted    The server accepts the score sent by the browser. This intentionally
             vulnerable version is used in class; each exploited flaw awards a flag.
  validated  The server tracks each game and calculates the score itself. This is
             the corrected version deployed at the end for comparison.

Uses only the Python standard library; no extra packages are required.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

MODE = os.environ.get("MODE", "trusted")
WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
GAME_DURATION_SECONDS = 10.0
MAX_CLICKS_PER_SECOND = 15
MAX_SCORE = int(GAME_DURATION_SECONDS * MAX_CLICKS_PER_SECOND)
VALID_NAME = re.compile(r"^[\w .-]{1,24}$")

FLAGS = {
    "impossible": "The server accepted a score above the human maximum",
    "no_browser": "The request was sent without using the browser",
    "hidden_route": "The client code revealed the admin reset route",
    "other_player": "Another player's score was modified",
}


@dataclass
class Player:
    score: int = 0
    flags: set[str] = field(default_factory=set)


@dataclass
class GameSession:
    name: str
    started_at: float
    clicks: int = 0
    last_click_at: float = 0.0


class GameState:
    """In-memory leaderboard and games protected by a lock for threaded requests."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.players: dict[str, Player] = {}
        self.games: dict[str, GameSession] = {}

    def get_player(self, name: str) -> Player:
        return self.players.setdefault(name, Player())

    def leaderboard(self) -> list[dict]:
        with self._lock:
            ordered_players = sorted(self.players.items(), key=lambda item: -item[1].score)
            return [
                {"name": name, "score": player.score, "flags": sorted(player.flags)}
                for name, player in ordered_players[:20]
            ]

    def record_score(
        self,
        name: str,
        score: int,
        flags: set[str] | frozenset[str] = frozenset(),
    ) -> None:
        with self._lock:
            player = self.get_player(name)
            player.score = max(player.score, score)
            player.flags |= flags

    def award_flag(self, name: str, flag: str) -> None:
        with self._lock:
            self.get_player(name).flags.add(flag)

    def reset(self) -> None:
        with self._lock:
            self.players.clear()
            self.games.clear()

    # In validated mode, each game is tracked on the server.
    def new_game(self, name: str) -> str:
        game_id = uuid.uuid4().hex
        with self._lock:
            self.games[game_id] = GameSession(name, time.monotonic())
        return game_id

    def record_click(self, game_id: str) -> int | None:
        """Count a click during the game if it is within the allowed rate."""
        now = time.monotonic()
        with self._lock:
            game = self.games.get(game_id)
            if game is None or now - game.started_at > GAME_DURATION_SECONDS:
                return None
            if now - game.last_click_at >= 1 / MAX_CLICKS_PER_SECOND:
                game.clicks += 1
                game.last_click_at = now
            return game.clicks

    def finish_game(self, game_id: str) -> int | None:
        with self._lock:
            game = self.games.pop(game_id, None)
        if game is None:
            return None
        self.record_score(game.name, game.clicks)
        return game.clicks


STATE = GameState()


class GameRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def log_message(self, format_string, *args):
        print(f"[{MODE}] {self.address_string()} {format_string % args}", flush=True)

    # Request helpers
    def _json(self, status: HTTPStatus, body: dict | list) -> None:
        encoded_body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded_body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded_body)

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length") or 0)
        if content_length == 0:
            return {}
        try:
            body = json.loads(self.rfile.read(content_length))
        except ValueError:
            return {}
        return body if isinstance(body, dict) else {}

    def _is_browser_request(self) -> bool:
        return self.headers.get("X-Game") == "browser"

    @staticmethod
    def _valid_name(value) -> str | None:
        return value if isinstance(value, str) and VALID_NAME.match(value) else None

    # API routes
    def do_GET(self):
        path, query = urlsplit(self.path).path, parse_qs(urlsplit(self.path).query)
        if path == "/api/leaderboard":
            return self._json(
                HTTPStatus.OK,
                {"mode": MODE, "max_score": MAX_SCORE, "leaderboard": STATE.leaderboard()},
            )
        if path == "/api/admin/reset":
            return self._reset(self._valid_name(query.get("name", [""])[0]))
        return super().do_GET()

    def do_POST(self):
        path = urlsplit(self.path).path
        data = self._read_json_body()
        name = self._valid_name(data.get("name"))

        if path == "/api/game":
            if name is None:
                return self._json(HTTPStatus.BAD_REQUEST, {"error": "Invalid name"})
            if MODE == "validated":
                return self._json(
                    HTTPStatus.OK,
                    {"game_id": STATE.new_game(name), "duration": GAME_DURATION_SECONDS},
                )
            return self._json(HTTPStatus.OK, {"duration": GAME_DURATION_SECONDS})

        if path == "/api/click" and MODE == "validated":
            score = STATE.record_click(str(data.get("game_id", "")))
            if score is None:
                return self._json(
                    HTTPStatus.GONE,
                    {"error": "Game has ended or does not exist"},
                )
            return self._json(HTTPStatus.OK, {"score": score})

        if path == "/api/finish" and MODE == "validated":
            score = STATE.finish_game(str(data.get("game_id", "")))
            if score is None:
                return self._json(
                    HTTPStatus.GONE,
                    {"error": "Game has ended or does not exist"},
                )
            return self._json(HTTPStatus.OK, {"score": score})

        if path == "/api/score" and MODE == "trusted":
            if name is None or not isinstance(data.get("score"), int):
                return self._json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "Name or score is missing"},
                )
            score = data["score"]
            earned_flags = set()
            if score > MAX_SCORE:
                earned_flags.add("impossible")
            if not self._is_browser_request():
                earned_flags.add("no_browser")
            STATE.record_score(name, score, earned_flags)
            return self._json(
                HTTPStatus.OK,
                {"ok": True, "flags": sorted(earned_flags)},
            )

        if path == "/api/admin/reset":
            return self._reset(name)

        return self._json(HTTPStatus.NOT_FOUND, {"error": "Unknown route"})

    def do_PUT(self):
        path_parts = urlsplit(self.path).path.split("/")
        if MODE == "trusted" and len(path_parts) == 4 and path_parts[1:3] == ["api", "score"]:
            target = self._valid_name(path_parts[3])
            data = self._read_json_body()
            author = self._valid_name(data.get("author"))
            if target is None or author is None or not isinstance(data.get("score"), int):
                return self._json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "Author or score is missing"},
                )
            STATE.record_score(target, data["score"])
            if target != author:
                STATE.award_flag(author, "other_player")
            return self._json(HTTPStatus.OK, {"ok": True})
        return self._json(HTTPStatus.NOT_FOUND, {"error": "Unknown route"})

    def _reset(self, name: str | None):
        if MODE != "trusted":
            return self._json(
                HTTPStatus.FORBIDDEN,
                {"error": "Only the instructor can reset the game"},
            )
        STATE.reset()
        if name:
            STATE.award_flag(name, "hidden_route")
        return self._json(HTTPStatus.OK, {"ok": True, "reset_by": name})


if __name__ == "__main__":
    print(f'"Hack the Leaderboard" running in {MODE} mode at http://localhost:8080', flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8080), GameRequestHandler).serve_forever()
