from typing import Optional, Callable
from .workspace import PruningWorkspace
from .graph_analyser import GraphAnalyser

class TreePruner:
    def __init__(self, main_db_path: str, workspace_db_path: Optional[str] = None):
        """Initialize the tree pruner.
        
        Args:
            main_db_path: Path to the main opening tree database
            workspace_db_path: Optional path for the temporary workspace database
        """
        self.main_db_path = main_db_path
        self.workspace_db_path = workspace_db_path
        
    def prune_single_game_positions(self, 
                                   max_distance: int = 5,
                                   batch_size: int = 1000,
                                   progress_callback: Optional[Callable[[str, int], None]] = None):
        """Prune single-game positions that are too far from core positions.
        
        Args:
            max_distance: Maximum allowed distance from core positions
            batch_size: Number of positions to process in each batch
            progress_callback: Optional callback function(stage: str, count: int)
                              for progress tracking
        """
        with PruningWorkspace(self.main_db_path, self.workspace_db_path) as workspace:
            # Initialize workspace with single-game positions
            workspace.initialise_closeness()
            if progress_callback:
                count = self._count_positions(workspace)
                progress_callback("Initialized workspace", count)
            
            # Calculate closeness to core positions
            analyser = GraphAnalyser(workspace.conn)
            analyser.calculate_closeness(max_distance, batch_size)
            if progress_callback:
                count = self._count_marked_positions(workspace)
                progress_callback("Calculated position closeness", count)
            
            # Mark positions for deletion
            workspace.mark_positions_for_deletion(max_distance)
            if progress_callback:
                count = self._count_positions_to_delete(workspace)
                progress_callback("Marked positions for deletion", count)
            
            # Delete positions in batches
            total_deleted = self._execute_batch_deletion(workspace, batch_size, progress_callback)
            
            if progress_callback:
                progress_callback("Completed deletions", total_deleted)
            
            # Vacuum the database to reclaim space
            workspace.conn.execute("VACUUM main_tree")
            
            if progress_callback:
                progress_callback("Database compacted", total_deleted)
    
    def _count_positions(self, workspace: PruningWorkspace) -> int:
        """Count total positions being analyzed."""
        return workspace.conn.execute(
            "SELECT COUNT(*) FROM position_closeness"
        ).fetchone()[0]
    
    def _count_marked_positions(self, workspace: PruningWorkspace) -> int:
        """Count positions that have been processed."""
        return workspace.conn.execute(
            "SELECT COUNT(*) FROM position_closeness WHERE processed = TRUE"
        ).fetchone()[0]
    
    def _count_positions_to_delete(self, workspace: PruningWorkspace) -> int:
        """Count positions marked for deletion."""
        return workspace.conn.execute(
            "SELECT COUNT(*) FROM positions_to_delete"
        ).fetchone()[0]
    
    def _execute_batch_deletion(self,
                               workspace: PruningWorkspace,
                               batch_size: int,
                               progress_callback: Optional[Callable[[str, int], None]] = None) -> int:
        """Execute the deletion of marked positions in batches, starting with leaf nodes.
        
        Returns:
            Total number of positions deleted
        """
        total_deleted = 0
        
        while True:
            with workspace.transaction() as conn:
                # Get next batch of leaf positions to delete (positions that are only destinations)
                positions = conn.execute(
                    """SELECT ptd.position_id 
                       FROM positions_to_delete ptd
                       WHERE NOT EXISTS (
                           SELECT 1 FROM main_tree.moves m 
                           WHERE m.from_position_id = ptd.position_id
                       )
                       LIMIT ?""", 
                    (batch_size,)
                ).fetchall()
                
                if not positions:
                    # If no leaf positions left, get any remaining positions
                    positions = conn.execute(
                        """SELECT position_id FROM positions_to_delete 
                           LIMIT ?""", 
                        (batch_size,)
                    ).fetchall()
                    
                    if not positions:
                        break
                    
                position_ids = [p[0] for p in positions]
                placeholders = ",".join("?" * len(position_ids))
                
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
                
                # Remove deleted positions from tracking table
                conn.execute(
                    f"DELETE FROM positions_to_delete WHERE position_id IN ({placeholders})",
                    position_ids
                )
                
                batch_count = len(position_ids)
                total_deleted += batch_count
                
                if progress_callback:
                    progress_callback("Deleting positions", total_deleted)
        
        return total_deleted