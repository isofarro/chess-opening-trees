# Database Structure

The opening tree database is made up of four tables:

## 1. `positions` table

The graph node table. This stores a normalised FEN string, and assigns a position id. This is the position id that is used in the other tables.

Two fields:
* `id` -- used to reference this position in keys
* `fen` -- the normalised FEN string for this position

## 2. `moves` table

The graph edges table.  This stores the moves in the game. The `from_position_id` and `to_position_id` are the ids of the positions in the `positions` table.

Three fields:
* `id` -- used to reference this move in keys
* `from_position_id` -- the id of the position that the move is from
* `to_position_id` -- the id of the position that the move is to

## 3. `position_stats` table

A table that aggregates the statistics for a position.

Fields:
* `position_id` -- the id of the position that the stats are for
* `total_games` -- the number of games reaching this position
* `white_wins` -- the number of games won by white
* `black_wins` -- the number of games won by black
* `draws` -- the number of games ended in a draw
* `total_player_elo` -- the sum of the player's elo for all games reaching this position
* `total_player_performance` -- the sum of the player's performance rating for all games reaching this position
* `last_played_date` -- the date of the last game played at this position

This aggregated data can then be used to calculate:

* The average rating of the player reaching this position
* The average rating peformance, based on the opponent's rating and the score
* The difference between the rating and performance, to show whether a player over- or under-performs with the played move.
* WDL stats expressed as a percentage

## 4. `imported_pgn_files`

A list of PGN files imported into this chess tree, with last-modified and file-hash values so we can detect whether we've imported the existing file or not.

