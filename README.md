Chess Opening Trees
===================

Creates opening trees from PGN files. The tree is an SQLite database.


## Python and uv set-up

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install uv
```

## Installation

```bash
git clone https://github.com/isofarro/chess-opening-trees.git
cd chess-opening-trees
uv install
```

## Usage


### Building a tree from PGN files

We build a tree from one or more PGN files. We can run the build repeatedly until
all the PGN files we want to add are added. This means we can update the opening
tree regularly, as new game databases are available.

```bash
./tree.py build \
    --tree my_tree.tree \
    --max-ply 60 \
    --min-rating 2000 \
    pgn/
```

The build keeps track of files it's imported, and skips them if there are no changes (file modification date, content hash). So you can run it multiple times against a directory, and it imports any new files found in the directory. Perfect for regularly updating a tree with weekly TWIC files.

### Pruning the tree of one game positions to a specific depth

This removes positions that have been visited once, and not within a specific
depth of the last position with more than one game.

```bash
./tree.py prune \
    my_tree.tree \
    --max-closeness 5
    --batch-size 2000
```

* `--max-closeness` is the number of plies from a position that has more than 1 visit. Defaults to 5.
* `--batch-size` is the number of positions to delete in each transaction. defaults to 1000.

Each 1-game position has a game reference, so it's feasible when the tree grows to reach the leaf position to re-process the game and add in some more moves.

## Opening tree queries

Query the opening tree by position

```bash
./tree.py query
    my_tree.tree
    --fen "r1bq1rk1/2p1bppp/p1np1n2/1p2p3/4P3/1BP2N1P/PP1P1PP1/RNBQR1K1 b - - 0 9"
    --output json
```

- `fen` is the FEN string of the position
- `output` is the format of the output. Defaults to `json`.

The JSON output looks like this:

```json
{
  "fen": "rn1qkb1r/ppp1pppp/5nb1/4N3/3P2P1/2N4P/PPP5/R1BQKB1R b KQkq -",
  "moves": [
    {
      "move": "e6",
      "fen": "rn1qkb1r/ppp2ppp/4pnb1/4N3/3P2P1/2N4P/PPP5/R1BQKB1R w KQkq -",
      "total_games": 3333,
      "white_wins": 2006,
      "draws": 160,
      "black_wins": 1167,
      "last_played_date": "2025-05-31",
      "rating": 2154,
      "performance": 2059
    },
    ...
  ]
}
 ```

## HTTP JSON API

### Using command line arguments

```bash
    ./tree.py serve \
    --trees bdg-cce pgn/openings/D00-bdg-games-cce-2025-05.tree \
    --port 2882
```

### Using a configuration file

```bash
    ./tree.py serve --config serve-config.json
```

The configuration file is in JSON format:

```json
{
  "port": 3000,
  "trees": [
    {
      "name": "main",
      "path": "twic-2025.tree"
    },
    {
      "name": "bdg",
      "path": "pgn/openings/D00-bdg-games-cce-2025-05.tree"
    }
  ]
}
```

Both methods start an HTTP server. The server supports multiple trees, each specified by name and tree file path. Command line arguments take precedence over config file settings.

The URL to query a position in an opening
tree is the pattern `http://localhost:2882/{tree}/{fen}` where:

* `{tree}` is the name of the tree defined in the `serve` command
* `{fen}` is the FEN string of the position, URL encoded.

```bash
curl http://localhost:2882/bdg-cce/rn1qkb1r%2Fpp2pppp%2F2p2n2%2F8%2F3P4%2F2N2Q1P%2FPPP3P1%2FR1B1KB1R%20w%20KQkq%20-%200%208
```

This returns a JSON response in the same structure as the `query` command above.

We can get a list of trees by doing a GET on `http://localhost:2882/`, this returns
the payload:

```json
[
  {
    "name": "main",
    "path": "http://localhost:2882/main/{fen}"
  },
  {
    "name": "bdg-cce",
    "path": "http://localhost:2882/bdg-cce/{fen}"
  }
]
```
