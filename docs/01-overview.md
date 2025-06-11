This repository contains a Python script to generate a chess opening tree from a PGN file. We can continue to add to the opening tree by adding more PGN files.

The script uses the chess library to parse the PGN file and create the opening tree, and aggregates statistics for each position in the tree.

An opening tree is a directed cyclical graph, the positions are the nodes and the moves are the edges.

The opening tree is an SQLite database with the following tables:

- `positions`: each position in the tree. The fields include the position FEN and an id. We store statistics for each position in the `position_stats` table.
- `moves`: each move in the tree with the from position and the to position (the id's of the positions).
- `position_statistics`: statistics for each position. The fields are the position id, and column that is a JSON object with the statistics for the position.
