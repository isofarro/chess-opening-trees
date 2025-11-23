import path from "node:path";
import Database from "better-sqlite3";
import type { Database as BetterDatabase } from "better-sqlite3";
import type { MoveRow, PositionRow } from "../types";

export class OpeningTreeRepository {
  private db: BetterDatabase;

  constructor(treeFilePath: string) {
    const absolutePath = path.isAbsolute(treeFilePath)
      ? treeFilePath
      : path.resolve(treeFilePath);
    const uri = `file:${absolutePath}?immutable=1&mode=ro`;
    let db: BetterDatabase;
    try {
      db = new Database(uri, {
        readonly: true,
        fileMustExist: true,
      }) as unknown as BetterDatabase;
    } catch {
      db = new Database(absolutePath, {
        readonly: true,
        fileMustExist: true,
      }) as unknown as BetterDatabase;
    }
    this.db = db;
    this.db.pragma("query_only=ON");
  }

  getPositionByFen(fen: string): PositionRow | null {
    const stmt = this.db.prepare("SELECT id, fen FROM positions WHERE fen = ?");
    const row = stmt.get(fen) as PositionRow | undefined;
    return row ?? null;
  }

  getMovesFromPosition(positionId: number): MoveRow[] {
    const sql = `
      SELECT
        m.move,
        p.fen,
        s.total_games,
        s.white_wins,
        s.draws,
        s.black_wins,
        s.total_player_elo,
        s.total_player_performance,
        s.last_played_date,
        s.game_ref
      FROM moves m
      JOIN positions p ON m.to_position_id = p.id
      JOIN position_statistics s ON m.to_position_id = s.position_id
      WHERE m.from_position_id = ?
      ORDER BY s.total_games DESC
    `;
    const stmt = this.db.prepare(sql);
    return stmt.all(positionId) as MoveRow[];
  }
}
