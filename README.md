Chess Opening Trees
===================

Creates opening trees from PGN files. The tree is an SQLite database.


## Python and uv set-up

```
python3 -m venv .venv
source .venv/bin/activate
pip install uv
```

## Installation

```
git clone https://github.com/isofarro/chess-opening-trees.git
cd chess-opening-trees
uv install
```

## Usage


### Building a tree from PGN files

We build a tree from one or more PGN files. We can run the build repeatedly until
all the PGN files we want to add are added. This means we can update the opening
tree regularly, as new game databases are available.

```
./tree.py build \
    --db my_tree.db \
    --max-ply 60 \
    --min-rating 2000 \
    pgn/
```

### Pruning the tree of one game positions to a specific depth

This removes positions that have been visited once, and not within a specific
depth of the last position with more than one game.

```
./tree.py prune \
    my_tree.db \
    --max-closeness 5
    --batch-size 2000
```

* `--max-closeness` is the number of plies from a position that has more than 1 visit. Defaults to 5.
* `--batch-size` is the number of positions to delete in each transaction. defaults to 1000.


## Opening tree queries

Query the opening tree by position

```
./tree.py query
    my_tree.db
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
