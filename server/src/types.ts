export interface TreeConfigItem {
  name: string;
  file: string;
}

export interface ServerConfig {
  trees: TreeConfigItem[];
  baseUrl?: string;
}

export interface PositionRow {
  id: number;
  fen: string;
}

export interface MoveRow {
  move: string;
  fen: string;
  total_games: number;
  white_wins: number;
  draws: number;
  black_wins: number;
  total_player_elo: number;
  total_player_performance: number;
  last_played_date: string;
  game_ref: string;
}

export interface PositionResponse {
  fen: string;
  moves: Array<{
    move: string;
    fen: string;
    total_games: number;
    white_wins: number;
    draws: number;
    black_wins: number;
    last_played_date: string;
    game_ref: string;
    rating: number;
    performance: number;
  }>;
}
