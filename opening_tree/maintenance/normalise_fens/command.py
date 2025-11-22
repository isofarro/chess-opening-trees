from opening_tree.repository.database import OpeningTreeRepository
from opening_tree.service.fen_utils import normalise_fen


def fix_fens(args) -> None:
    repo = OpeningTreeRepository(args.tree)
    conn = repo.conn

    cursor = conn.execute("SELECT id, fen FROM positions")
    positions = cursor.fetchall()

    total = len(positions)
    fixed = 0
    merged = 0
    processed = 0
    progress_printed = False

    for old_id, fen in positions:
        processed += 1
        if processed % 20000 == 0:
            print("#", end="", flush=True)
            progress_printed = True
        try:
            new_fen = normalise_fen(fen)
        except Exception:
            continue

        if new_fen == fen:
            continue

        row = conn.execute("SELECT id FROM positions WHERE fen = ?", (new_fen,)).fetchone()

        if args.dry_run:
            if row is None:
                fixed += 1
                if getattr(args, "show_details", False):
                    print(f"UPDATE positions SET fen = '{new_fen}' WHERE id = {old_id}")
            else:
                merged += 1
                if getattr(args, "show_details", False):
                    print(f"MERGE position {old_id} -> {row[0]} ({fen} -> {new_fen})")
            continue

        conn.execute("BEGIN TRANSACTION")
        try:
            if row is None:
                conn.execute("UPDATE positions SET fen = ? WHERE id = ?", (new_fen, old_id))
                fixed += 1
            else:
                new_id = row[0]

                stats_row = conn.execute(
                    """
                    SELECT total_games, white_wins, black_wins, draws,
                           total_player_elo, total_player_performance,
                           last_played_date, game_ref
                    FROM position_statistics WHERE position_id = ?
                    """,
                    (old_id,)
                ).fetchone()

                if stats_row is not None:
                    conn.execute(
                        """
                        INSERT INTO position_statistics (
                            position_id, total_games, white_wins, black_wins, draws,
                            total_player_elo, total_player_performance, last_played_date, game_ref
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(position_id) DO UPDATE SET
                            total_games = total_games + excluded.total_games,
                            white_wins = white_wins + excluded.white_wins,
                            black_wins = black_wins + excluded.black_wins,
                            draws = draws + excluded.draws,
                            total_player_elo = total_player_elo + excluded.total_player_elo,
                            total_player_performance = total_player_performance + excluded.total_player_performance,
                            last_played_date = MAX(last_played_date, excluded.last_played_date),
                            game_ref = CASE
                                WHEN excluded.last_played_date > last_played_date THEN excluded.game_ref
                                ELSE game_ref
                            END
                        """,
                        (
                            new_id,
                            stats_row[0], stats_row[1], stats_row[2], stats_row[3],
                            stats_row[4], stats_row[5], stats_row[6], stats_row[7]
                        )
                    )

                rows = conn.execute(
                    "SELECT id, to_position_id, move FROM moves WHERE from_position_id = ?",
                    (old_id,)
                ).fetchall()
                for move_id, to_id, move_san in rows:
                    exists = conn.execute(
                        "SELECT id FROM moves WHERE from_position_id = ? AND to_position_id = ? AND move = ?",
                        (new_id, to_id, move_san)
                    ).fetchone()
                    if exists:
                        conn.execute("DELETE FROM moves WHERE id = ?", (move_id,))
                    else:
                        conn.execute(
                            "UPDATE moves SET from_position_id = ? WHERE id = ?",
                            (new_id, move_id)
                        )

                rows = conn.execute(
                    "SELECT id, from_position_id, move FROM moves WHERE to_position_id = ?",
                    (old_id,)
                ).fetchall()
                for move_id, from_id, move_san in rows:
                    exists = conn.execute(
                        "SELECT id FROM moves WHERE from_position_id = ? AND to_position_id = ? AND move = ?",
                        (from_id, new_id, move_san)
                    ).fetchone()
                    if exists:
                        conn.execute("DELETE FROM moves WHERE id = ?", (move_id,))
                    else:
                        conn.execute(
                            "UPDATE moves SET to_position_id = ? WHERE id = ?",
                            (new_id, move_id)
                        )

                conn.execute("DELETE FROM position_statistics WHERE position_id = ?", (old_id,))
                conn.execute("DELETE FROM positions WHERE id = ?", (old_id,))

                merged += 1

            conn.commit()
        except Exception:
            conn.rollback()
            raise

    if progress_printed:
        print()
    print(f"Processed positions: {total}")
    print(f"Updated FENs: {fixed}")
    print(f"Merged positions: {merged}")
    if not getattr(args, "dry_run", False):
        conn.execute("VACUUM")
