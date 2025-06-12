# Opening tree queries

```
./tree.py query
    my_tree.db
    --fen "r1bq1rk1/2p1bppp/p1np1n2/1p2p3/4P3/1BP2N1P/PP1P1PP1/RNBQR1K1 b - - 0 9"
    --output json
```

- `fen` is the FEN of the position to query. It could be the full FEN or the normalised one.
- `output` is the format of the output. Defaults to `json`.

Returns the moves and position statistics of the position reached after the move. For each move we return:

- the move
- the FEN of the resulting position
- total number of games reaching the from position
- number of white wins, draws, and black wins
- average rating of player making the move
- performance rating of the played move
- the last played date of the from position

The structure of the output in JSON is:

```json
{
    "fen": "r1bq1rk1/2p1bppp/p1np1n2/1p2p3/4P3/1BP2N1P/PP1P1PP1/RNBQR1K1 b - -",
    "moves": [
        {
            "move": "Na5",
            "fen": "r1bq1rk1/2p1bppp/p2p1n2/np2p3/4P3/1BP2N1P/PP1P1PP1/RNBQR1K1 w - -",
            "total_games": 9710,
            "white_wins": 3495,
            "draws": 4564,
            "black_wins": 1651,
            "rating": 2320,
            "performance": 2390,
            "last_played_date": "2025-01-03", 
        },
        ... other moves and stats from the given position...
    ],
}
```

