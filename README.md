# Minimal tournament

Minimal static tournament site generator using only Python standard library, JSON data files, HTML fragments, and one CSS file.

## Files

- `data/players.json`: player names and persisted Elo values
- `data/results.json`: completed matches in processing order
- `templates/page.html`: page skeleton with placeholders
- `templates/header.html`
- `templates/info.html`
- `templates/rules.html`
- `templates/footer.html`
- `scripts/generate.py`: validates results and regenerates `site/index.html`
- `site/images/`: deployable static image assets used by the page
- `site/style.css`: static styling
- `site/index.html`: generated output

## Input format

### `data/players.json`

```json
[
  { "name": "Avery", "elo": 1200 },
  { "name": "Blake", "elo": 1200 }
]
```

Rules:

- `name` is the player ID
- names must be unique and must match results exactly
- `elo` must be numeric
- Elo values are kept in this file and are not modified by the generator

### `data/results.json`

```json
[
  {
    "player_a": "Avery",
    "player_b": "Blake",
    "winner": "draw",
    "fleet_points": 72.5,
    "date": "2026-06-01"
  }
]
```

Rules:

- `winner` must equal either `player_a`, `player_b`, or `"draw"`
- `fleet_points` must be a non-negative number
- `date` must use `YYYY-MM-DD`
- each player pairing may appear only once, regardless of player order

## Usage

Run:

```sh
python3 scripts/generate.py
```

This will:

1. Validate the input files
2. Keep Elo values from `data/players.json` unchanged
3. Regenerate `site/index.html`

## Template placeholders

`templates/page.html` must contain these markers:

- `{{header}}`
- `{{info}}`
- `{{standings}}`
- `{{rules}}`
- `{{footer}}`

## Leaderboard matrix

The generated leaderboard is a head-to-head matrix:

1. Rows and columns are alphabetical by player name
2. Each cell shows the row player's score against the column player
3. Scores are rendered as `1`, `0.5`, or `0`
4. Unplayed cells are empty
5. Self-match cells use a distinct not-applicable style
