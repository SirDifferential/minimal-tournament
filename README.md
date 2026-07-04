# Minimal tournament

Minimal tool to run round robin tournaments and display its results on a webpage.

## Usage

* Populate data/players.json with player names. ELO scores are currently unused, but may be used in future for Swiss tournament formats.
* Write results in results.json like so:

```
[
	{
		"player_a": "TDNLT",
		"player_b": "Mothra",
		"winner": "Mothra",
		"fleet_points": 42,
		"date": "2026-06-29"
	},
	{
		"player_a": "Azak",
		"player_b": "Dittman Rat",
		"winner": "Azak",
		"fleet_points": 95,
		"date": "2026-06-30"
	}
]
```

* Run `python3 sripts/generate.py`
* Resulting html is in side/index.html

