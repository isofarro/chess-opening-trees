import os
import sqlite3
from contextlib import contextmanager
from typing import Optional
from opening_tree.maintenance.pruning.repository import PruningRepository

class PruningWorkspace:
    def __init__(self, repository):
        """Initialize a pruning workspace.

        Args:
            repository: The pruning repository instance
        """
        self.repository = repository

    def initialise_closeness(self):
        """Initialize the position_closeness table with single-game positions."""
        return self.repository.initialize_single_game_positions()

    def mark_positions_for_deletion(self, max_distance: int):
        """Mark positions that are too far from core positions for deletion."""
        return self.repository.mark_positions_for_deletion()

    @contextmanager
    def transaction(self):
        """Context manager for transactions in the workspace."""
        with self.repository.transaction() as conn:
            yield conn