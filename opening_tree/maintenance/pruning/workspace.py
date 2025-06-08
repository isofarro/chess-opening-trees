import os
import sqlite3
from contextlib import contextmanager
from typing import Optional

class PruningWorkspace:
    def __init__(self, main_db_path: str, workspace_db_path: Optional[str] = None):
        """Initialize a pruning workspace.
        
        Args:
            main_db_path: Path to the main opening tree database
            workspace_db_path: Path for the temporary workspace database.
                              If None, creates a temporary file.
        """
        self.main_db_path = main_db_path
        self.workspace_db_path = workspace_db_path or ':memory:'
        self.conn = None
        
    def __enter__(self):
        """Context manager entry point. Creates workspace and attaches main DB."""
        self.conn = sqlite3.connect(self.workspace_db_path)
        self._attach_main_db()
        self._create_schema()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point. Detaches main DB and closes workspace."""
        if self.conn:
            self._detach_main_db()
            self.conn.close()
            self.conn = None
            
    def _attach_main_db(self):
        """Attach the main database to the workspace."""
        self.conn.execute(
            'ATTACH DATABASE ? AS main_tree',
            (self.main_db_path,)
        )
        
    def _detach_main_db(self):
        """Detach the main database from the workspace."""
        self.conn.execute('DETACH DATABASE main_tree')
        
    def _create_schema(self):
        """Create the workspace schema for graph analysis."""
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

    def initialise_closeness(self):
        """Initialise the position_closeness table with single-game positions.
        These positions start with closeness 0 and will be updated as we
        discover their connection to core positions (positions with more
        than one game)."""
        with self.transaction() as conn:
            conn.execute("""
                INSERT INTO position_closeness (position_id, closeness)
                SELECT p.id, 0 as closeness
                FROM main_tree.positions p
                JOIN main_tree.position_statistics ps 
                    ON p.id = ps.position_id
                WHERE ps.total_games = 1
            """)
            
    def mark_positions_for_deletion(self, max_distance: int):
        """Mark positions that are too far from core positions for deletion.
        Positions with closeness = 0 are those that were never reached
        during the closeness calculation phase."""
        with self.transaction() as conn:
            conn.execute("""
                INSERT INTO positions_to_delete (position_id)
                SELECT position_id
                FROM position_closeness
                WHERE closeness = 0
            """)
        
    @contextmanager
    def transaction(self):
        """Context manager for transactions in the workspace."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise