#!/usr/bin/env python3

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
SITE_DIR = BASE_DIR / "site"

PLAYERS_PATH = DATA_DIR / "players.json"
RESULTS_PATH = DATA_DIR / "results.json"
OUTPUT_PATH = SITE_DIR / "index.html"
PAGE_TEMPLATE_PATH = TEMPLATES_DIR / "page.html"

DATE_FORMAT = "%Y-%m-%d"


@dataclass
class Player:
    name: str
    elo: float
    points: float = 0.0
    fleet_points: float = 0.0


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def load_players(path: Path) -> dict[str, Player]:
    raw_players = load_json(path)
    if not isinstance(raw_players, list):
        raise SystemExit("players.json must contain a JSON array")

    players: dict[str, Player] = {}
    for index, entry in enumerate(raw_players):
        if not isinstance(entry, dict):
            raise SystemExit(f"players.json entry {index} must be an object")
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            raise SystemExit(f"players.json entry {index} must include a non-empty string name")
        if name in players:
            raise SystemExit(f"Duplicate player name in players.json: {name}")

        elo_raw = entry.get("elo")
        if not isinstance(elo_raw, (int, float)):
            raise SystemExit(f"Invalid elo for player {name}: expected number")
        players[name] = Player(name=name, elo=float(elo_raw))

    if not players:
        raise SystemExit("players.json must contain at least one player")

    return players


def parse_date(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str):
        raise SystemExit(f"{field_name} must be a string in YYYY-MM-DD format")
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError as exc:
        raise SystemExit(f"{field_name} must use YYYY-MM-DD format: {value}") from exc


def load_results(path: Path, players: dict[str, Player]) -> list[dict[str, Any]]:
    raw_results = load_json(path)
    if not isinstance(raw_results, list):
        raise SystemExit("results.json must contain a JSON array")

    results: list[dict[str, Any]] = []
    seen_pairings: set[tuple[str, str]] = set()
    for index, entry in enumerate(raw_results):
        if not isinstance(entry, dict):
            raise SystemExit(f"results.json entry {index} must be an object")

        player_a = entry.get("player_a")
        player_b = entry.get("player_b")
        winner = entry.get("winner")
        fleet_points = entry.get("fleet_points")
        date_value = entry.get("date")

        for label, player_name in (("player_a", player_a), ("player_b", player_b), ("winner", winner)):
            if not isinstance(player_name, str) or not player_name.strip():
                raise SystemExit(f"results.json entry {index} must include a non-empty string {label}")

        if player_a == player_b:
            raise SystemExit(f"results.json entry {index} has a self-match for {player_a}")
        if player_a not in players:
            raise SystemExit(f"results.json entry {index} references unknown player: {player_a}")
        if player_b not in players:
            raise SystemExit(f"results.json entry {index} references unknown player: {player_b}")
        if winner not in (player_a, player_b, "draw"):
            raise SystemExit(
                f"results.json entry {index} winner must match player_a, player_b, or draw: {winner}"
            )
        if not isinstance(fleet_points, (int, float)) or fleet_points < 0:
            raise SystemExit(f"results.json entry {index} fleet_points must be a non-negative number")

        pairing = tuple(sorted((player_a, player_b)))
        if pairing in seen_pairings:
            raise SystemExit(
                f"results.json entry {index} duplicates an existing pairing: {player_a} vs {player_b}"
            )
        seen_pairings.add(pairing)

        parsed_date = parse_date(date_value, f"results.json entry {index} date")
        results.append(
            {
                "player_a": player_a,
                "player_b": player_b,
                "winner": winner,
                "fleet_points": float(fleet_points),
                "date": parsed_date,
            }
        )

    return results
def apply_results(players: dict[str, Player], results: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    matrix_results: dict[tuple[str, str], str] = {}
    for entry in results:
        player_a = players[entry["player_a"]]
        player_b = players[entry["player_b"]]
        winner_name = entry["winner"]
        fleet_points = entry["fleet_points"]

        if winner_name == "draw":
            score_a = 0.5
            score_b = 0.5
        else:
            score_a = 1.0 if winner_name == player_a.name else 0.0
            score_b = 1.0 if winner_name == player_b.name else 0.0

        player_a.points += score_a
        player_b.points += score_b

        if winner_name == player_a.name:
            player_a.fleet_points += fleet_points
        elif winner_name == player_b.name:
            player_b.fleet_points += fleet_points

        matrix_results[(player_a.name, player_b.name)] = format_score(score_a)
        matrix_results[(player_b.name, player_a.name)] = format_score(score_b)

    return matrix_results


def format_score(value: float) -> str:
    if value == 1.0:
        return "1"
    if value == 0.5:
        return "0.5"
    return "0"


def abbreviate_name(name: str) -> str:
    parts = name.split()
    if len(parts) > 1:
        return "".join(part[0] for part in parts if part)
    return name[:3]


def render_standings(players: dict[str, Player], matrix_results: dict[tuple[str, str], str]) -> str:
    ordered_players = sorted(players.values(), key=lambda player: (player.name.casefold(), player.name))

    points_label = "points (fleet points)"
    escaped_points_label = escape(points_label)

    header_cells = ["<th>Player</th>"]
    for opponent in ordered_players:
        header_cells.append(
            f'<th class="matrix-opponent" title="{escape(opponent.name)}" aria-label="{escape(opponent.name)}">'
            f'<abbr title="{escape(opponent.name)}">{escape(abbreviate_name(opponent.name))}</abbr>'
            "</th>"
        )
    header_cells.append(
        f'<th class="matrix-points matrix-divider" title="{escaped_points_label}" '
        f'aria-label="{escaped_points_label}">Points</th>'
    )

    rows = []
    for player in ordered_players:
        cells = [
            f'<th scope="row" class="matrix-player">{escape(player.name)}</th>',
        ]
        for opponent in ordered_players:
            matchup_label = f"{player.name} vs {opponent.name}"
            if player.name == opponent.name:
                cells.append(
                    f'<td class="matrix-cell matrix-cell--na" title="{escape(matchup_label)}" '
                    f'aria-label="{escape(matchup_label)}"></td>'
                )
                continue

            result = matrix_results.get((player.name, opponent.name), "")
            cells.append(
                f'<td class="matrix-cell" title="{escape(matchup_label)}" aria-label="{escape(matchup_label)}">'
                f'{escape(result)}</td>'
            )
        cells.append(
            f'<td class="matrix-points matrix-divider" title="{escaped_points_label}" '
            f'aria-label="{escaped_points_label}">'
            f'{format_summary(player.points, player.fleet_points)}</td>'
        )

        rows.append(f"<tr>{''.join(cells)}</tr>")

    return (
        '<section class="panel" id="standings">'
        "<div class=\"section-heading\">"
        "<p class=\"eyebrow\">Scoreboard</p>"
        "</div>"
        "<div class=\"table-wrap table-wrap--matrix\">"
        '<table class="matrix-table">'
        f"<thead><tr>{''.join(header_cells)}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        "</div>"
        "</section>"
    )


def format_points(value: float) -> str:
    return f"{value:g}"


def format_summary(points: float, fleet_points: float) -> str:
    return f"{format_points(points)} ({format_points(fleet_points)})"


def escape(value: str) -> str:
    return html.escape(value, quote=True)


def load_template(name: str) -> str:
    path = TEMPLATES_DIR / name
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing required template: {path}") from exc


def render_page(standings_html: str) -> str:
    page = load_template("page.html")
    replacements = {
        "{{header}}": load_template("header.html"),
        "{{info}}": load_template("info.html"),
        "{{rules}}": load_template("rules.html"),
        "{{standings}}": standings_html,
        "{{footer}}": load_template("footer.html").replace(
            "{{generated_at}}",
            escape(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")),
        ),
    }

    for placeholder, content in replacements.items():
        if placeholder not in page:
            raise SystemExit(f"Template placeholder missing from page.html: {placeholder}")
        page = page.replace(placeholder, content)

    return page


def main() -> None:
    players = load_players(PLAYERS_PATH)
    results = load_results(RESULTS_PATH, players)
    matrix_results = apply_results(players, results)

    standings_html = render_standings(players, matrix_results)
    page_html = render_page(standings_html)

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(page_html, encoding="utf-8")


if __name__ == "__main__":
    main()
