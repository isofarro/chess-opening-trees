from contextlib import contextmanager
from typing import List, Tuple

class PruningRepository:
    def __init__(self, conn):
        self.conn = conn

    def attach_main_database(self, main_tree_path: str):
        """Attach the main database for pruning operations."""
        self.conn.execute('ATTACH DATABASE ? AS main_tree', (main_tree_path,))

    def detach_main_database(self):
        """Detach the main database after pruning operations."""
        self.conn.execute('DETACH DATABASE main_tree')

    def create_schema(self):
        """Create the workspace schema for pruning operations."""
        self.conn.executescript("""
            -- Track positions and their closeness to core nodes
            CREATE TABLE position_closeness (
                position_id INTEGER PRIMARY KEY,
                closeness INTEGER DEFAULT 0,
                processed BOOLEAN DEFAULT FALSE
            );

            -- Index for efficient closeness updates
            CREATE INDEX idx_position_closeness_unprocessed
            ON position_closeness(processed, closeness);

            -- Track positions that need to be deleted
            CREATE TABLE positions_to_delete (
                position_id INTEGER PRIMARY KEY
            );
        """)

    def count_positions(self) -> int:
        """Count total positions being analyzed."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM position_closeness")
        return cursor.fetchone()[0]

    def count_marked_positions(self) -> int:
        """Count positions marked for deletion."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM position_closeness WHERE processed = TRUE")
        return cursor.fetchone()[0]

    def count_positions_to_delete(self) -> int:
        """Count positions marked for deletion."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM positions_to_delete")
        return cursor.fetchone()[0]

    def initialize_single_game_positions(self) -> int:
        """Initialize position_closeness table with single-game positions.
        Returns number of positions initialized."""
        with self.transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO position_closeness (position_id, closeness)
                SELECT p.id, 0 as closeness
                FROM main_tree.positions p
                JOIN main_tree.position_statistics ps
                    ON p.id = ps.position_id
                WHERE ps.total_games = 1
            """)
            return cursor.rowcount

    def mark_positions_near_core(self, initial_closeness: int, batch_size: int) -> int:
        """Mark positions directly reachable from core positions.
        Returns number of positions updated."""
        with self.transaction() as conn:
            cursor = conn.execute("""
                WITH reachable AS (
                    SELECT DISTINCT m.to_position_id as position_id
                    FROM main_tree.moves m
                    JOIN main_tree.position_statistics ps
                        ON m.from_position_id = ps.position_id
                    WHERE ps.total_games > 1
                    AND EXISTS (
                        SELECT 1 FROM position_closeness target
                        WHERE target.position_id = m.to_position_id
                        AND target.closeness = 0
                        AND target.processed = FALSE
                    )
                    LIMIT ?
                )
                UPDATE position_closeness
                SET closeness = ?, processed = TRUE
                WHERE position_id IN (SELECT position_id FROM reachable)
                AND closeness = 0
                AND processed = FALSE
            """, (batch_size, initial_closeness))
            return conn.total_changes

    def update_closeness_batch(self, current_closeness: int, batch_size: int) -> int:
        """Update closeness for positions reachable from higher closeness positions.
        Returns number of positions updated."""
        with self.transaction() as conn:
            cursor = conn.execute("""
                WITH reachable AS (
                    SELECT DISTINCT m.to_position_id as position_id
                    FROM main_tree.moves m
                    JOIN position_closeness pd
                        ON m.from_position_id = pd.position_id
                    WHERE pd.closeness = ?
                    AND EXISTS (
                        SELECT 1 FROM position_closeness target
                        WHERE target.position_id = m.to_position_id
                        AND target.closeness = 0
                        AND target.processed = FALSE
                    )
                    LIMIT ?
                )
                UPDATE position_closeness
                SET closeness = ?, processed = TRUE
                WHERE position_id IN (SELECT position_id FROM reachable)
                AND closeness = 0
                AND processed = FALSE
            """, (current_closeness + 1, batch_size, current_closeness))
            return conn.total_changes

    def mark_positions_for_deletion(self) -> int:
        """Mark unreachable positions for deletion.
        Returns number of positions marked."""
        with self.transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO positions_to_delete (position_id)
                SELECT position_id
                FROM position_closeness
                WHERE closeness = 0
            """)
            return cursor.rowcount

    def get_leaf_positions_for_deletion(self, batch_size: int) -> List[int]:
        """Get a batch of leaf positions (no outgoing moves) marked for deletion."""
        cursor = self.conn.execute("""
            SELECT ptd.position_id
            FROM positions_to_delete ptd
            WHERE NOT EXISTS (
                SELECT 1 FROM main_tree.moves m
                WHERE m.from_position_id = ptd.position_id
            )
            LIMIT ?
        """, (batch_size,))
        return [row[0] for row in cursor.fetchall()]

    def get_positions_for_deletion(self, batch_size: int) -> List[int]:
        """Get a batch of any positions marked for deletion."""
        cursor = self.conn.execute("""
            SELECT position_id FROM positions_to_delete
            LIMIT ?
        """, (batch_size,))
        return [row[0] for row in cursor.fetchall()]

    def delete_positions(self, position_ids: List[int]):
        """Delete the specified positions and their related data."""
        if not position_ids:
            return

        placeholders = ",".join("?" * len(position_ids))
        with self.transaction() as conn:
            # Delete from dependent tables first
            conn.execute(
                f"DELETE FROM main_tree.moves WHERE from_position_id IN ({placeholders}) "
                f"OR to_position_id IN ({placeholders})",
                position_ids * 2
            )

            conn.execute(
                f"DELETE FROM main_tree.position_statistics WHERE position_id IN ({placeholders})",
                position_ids
            )

            conn.execute(
                f"DELETE FROM main_tree.positions WHERE id IN ({placeholders})",
                position_ids
            )

            conn.execute(
                f"DELETE FROM positions_to_delete WHERE position_id IN ({placeholders})",
                position_ids
            )

    def vacuum_database(self):
        """Vacuum the main database to reclaim space."""
        self.conn.execute("VACUUM main_tree")

    @contextmanager
    def transaction(self):
        """Context manager for transactions."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise