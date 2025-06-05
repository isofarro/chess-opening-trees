Chess Opening Trees
===================

This repository contains a Python script to generate a chess opening tree from a PGN file. We can continue to add to the opening tree by adding more PGN files.

The script uses the chess library to parse the PGN file and create the opening tree, and aggregates statistics for each position in the tree.

An opening tree is a directed cyclical graph, the positions are the nodes and the moves are the edges.

The opening tree is an SQLite database with the following tables:

- `positions`: each position in the tree. The fields include the position FEN and an id. We store statistics for each position in the `position_stats` table.
- `moves`: each move in the tree with the from position and the to position (the id's of the positions).
- `position_statistics`: statistics for each position. The fields are the position id, and column that is a JSON object with the statistics for the position.

The statistics we want to aggregate for a position are:
- The number of games that reach the position.
- The number of games that end in a win.
- The number of games that end in a loss.
- The number of games that end in a draw.
- The average rating of the side that reaches the position. (We sum all the player ratings and store that value. When we want the average rating, we can divide by the number of games reaching the position.)
- average rating of the side that ends the game. (We aggregate the player's rating, and divide by the number of games that end the game at render time.)
- the most recent date the position was reached.

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

```
python -m opening_tree.tree build \
    --db my_tree.db \
    --max-ply 60 \
    --min-rating 2000 \
    ~/Downloads/twic1594.pgn 
```