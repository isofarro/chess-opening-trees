function expandFenRank(rankStr: string): string {
	const joined = rankStr
		.split("")
		.map((ch) => (/^[0-9]$/.test(ch) ? " ".repeat(Number(ch)) : ch))
		.join("");
	return (joined + " ".repeat(8)).slice(0, 8);
}

function normaliseEnPassant(
	ep: string,
	piecePlacement: string,
	activeColor: string,
): string {
	if (ep === "-") return ep;
	if (!/^[a-h][36]$/.test(ep)) return ep;
	const fileIdx = ep.charCodeAt(0) - 97;
	const isWhiteToMove = activeColor === "w";
	const pawnChar = isWhiteToMove ? "P" : "p";
	const pawnRankIdx = 8 - (isWhiteToMove ? 5 : 4);
	const ranks = piecePlacement.split("/");
	const rankExpanded = expandFenRank(ranks[pawnRankIdx]);
	const leftOk = fileIdx - 1 >= 0 && rankExpanded[fileIdx - 1] === pawnChar;
	const rightOk = fileIdx + 1 <= 7 && rankExpanded[fileIdx + 1] === pawnChar;
	return leftOk || rightOk ? ep : "-";
}

export function isLegalEnPassant(fen: string): boolean {
	const parts = fen.trim().split(/\s+/).filter(Boolean);
	if (parts.length < 4) return false;
	const ep = parts[3];
	if (ep === "-") return false;
	return normaliseEnPassant(ep, parts[0], parts[1]) === ep;
}

export function normaliseFen(fen: string): string {
	const parts = fen.trim().split(/\s+/).filter(Boolean);
	if (parts.length < 4)
		throw new Error(`Invalid FEN string: insufficient parts - ${fen}`);
	const [piecePlacement, activeColor, castlingRights, enPassantTarget] = parts;
	const ep = normaliseEnPassant(enPassantTarget, piecePlacement, activeColor);
	return `${piecePlacement} ${activeColor} ${castlingRights} ${ep}`;
}
