from typing import Optional

class GraphAnalyser:
    def __init__(self, workspace_conn):
        """Initialize the graph analyser.
        
        Args:
            workspace_conn: SQLite connection to the pruning workspace
        """
        self.conn = workspace_conn
        
    def calculate_closeness(self, max_steps: int = 5, batch_size: int = 1000):
        """Calculate closeness to core positions (positions with more than one game)
        by traversing the move graph forward. Positions closer to core positions
        will have higher closeness values.
        
        Args:
            max_steps: Maximum steps away from core positions to consider
            batch_size: Number of positions to process in each batch
        """
        # First, identify positions directly reachable from core positions
        positions_updated = self._mark_positions_near_core(max_steps, batch_size)
        if not positions_updated:
            return
            
        # Then propagate closeness values to positions reachable from those
        remaining_steps = max_steps - 1
        while remaining_steps > 0:
            positions_updated = self._update_closeness_batch(remaining_steps, batch_size)
            if not positions_updated:
                break
            remaining_steps -= 1
            
    def _mark_positions_near_core(self, initial_closeness: int, batch_size: int) -> int:
        """Mark positions that can be reached directly from core positions.
        These positions get the highest closeness value.
        
        Args:
            initial_closeness: Starting closeness value (max_steps)
            batch_size: Maximum number of positions to process
            
        Returns:
            Number of positions updated
        """
        with self.conn:
            cursor = self.conn.execute("""
                WITH reachable AS (
                    -- Get single-game positions reachable from core positions
                    SELECT DISTINCT m.to_position_id as position_id
                    FROM main_tree.moves m
                    JOIN main_tree.position_statistics ps 
                        ON m.from_position_id = ps.position_id
                    WHERE ps.total_games > 1
                    -- Only include positions we're tracking
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
            
            return self.conn.total_changes
            
    def _update_closeness_batch(self, closeness: int, batch_size: int) -> int:
        """Update closeness for a batch of positions that can be reached from
        positions with higher closeness in one move.
        
        Args:
            closeness: Closeness value to assign (decrements as we get further from core)
            batch_size: Maximum number of positions to process in this batch
            
        Returns:
            Number of positions updated in this batch
        """
        with self.conn:
            cursor = self.conn.execute("""
                WITH reachable AS (
                    -- Get positions reachable from positions with higher closeness
                    SELECT DISTINCT m.to_position_id as position_id
                    FROM main_tree.moves m
                    JOIN position_closeness pd 
                        ON m.from_position_id = pd.position_id
                    WHERE pd.closeness = ?
                    -- Only include unprocessed positions we're tracking
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
            """, (closeness + 1, batch_size, closeness))
            
            return self.conn.total_changes
