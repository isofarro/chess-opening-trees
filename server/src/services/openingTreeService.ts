import type { OpeningTreeRepository } from "../repository/openingTreeRepository";
import type { MoveRow, PositionResponse } from "../types";
import { normaliseFen } from "../utils/fen";

function removeEnPassantFromFen(fen: string): string {
	const parts = fen.split(/\s+/);
	if (parts.length >= 4) parts[3] = "-";
	return parts.slice(0, 4).join(" ");
}

function mergeMoves(moves1: MoveRow[], moves2: MoveRow[]): MoveRow[] {
	const dict = new Map<string, MoveRow>();
	for (const m of moves1) dict.set(m.move, { ...m });
	for (const m of moves2) if (!dict.has(m.move)) dict.set(m.move, { ...m });
	return Array.from(dict.values());
}

export class OpeningTreeService {
	constructor(private repo: OpeningTreeRepository) {}

	queryPosition(fen: string): PositionResponse | null {
		const normalized = normaliseFen(fen);
		const position = this.repo.getPositionByFen(normalized);
		if (!position) return null;

		let moves = this.repo.getMovesFromPosition(position.id);

		const parts = normalized.split(/\s+/);
		const hasEp = parts.length >= 4 && parts[3] !== "-";
		if (hasEp) {
			const noEpFen = removeEnPassantFromFen(normalized);
			const noEpPos = this.repo.getPositionByFen(noEpFen);
			if (noEpPos) {
				const noEpMoves = this.repo.getMovesFromPosition(noEpPos.id);
				moves = mergeMoves(moves, noEpMoves);
			}
		}

		const transformed = moves.map((move: MoveRow) => {
			const rating = Math.trunc(move.total_player_elo / move.total_games);
			const performance = Math.trunc(
				move.total_player_performance / move.total_games,
			);
			return {
				move: move.move,
				fen: move.fen,
				total_games: move.total_games,
				white_wins: move.white_wins,
				draws: move.draws,
				black_wins: move.black_wins,
				last_played_date: move.last_played_date,
				game_ref: move.game_ref,
				rating,
				performance,
			};
		});

		transformed.sort((a, b) => b.total_games - a.total_games);

		return {
			fen: position.fen,
			moves: transformed,
		};
	}
}
