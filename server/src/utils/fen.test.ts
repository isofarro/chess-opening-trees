import { describe, expect, it } from "vitest";
import { normaliseFen } from "./fen";

describe("normaliseFen", () => {
  it("removes move counters", () => {
    const input =
      "r1bq1rk1/2p1bppp/p1np1n2/1p2p3/4P3/1BP2N1P/PP1P1PP1/RNBQR1K1 b - - 0 9";
    const expected =
      "r1bq1rk1/2p1bppp/p1np1n2/1p2p3/4P3/1BP2N1P/PP1P1PP1/RNBQR1K1 b - -";
    expect(normaliseFen(input)).toBe(expected);
  });

  it("resets en-passant when not capturable", () => {
    const input =
      "r1bqk2r/2ppbppp/p1n2n2/1p2p3/B3P3/5N2/PPPP1PPP/RNBQR1K1 w kq b6 0 7";
    const expected =
      "r1bqk2r/2ppbppp/p1n2n2/1p2p3/B3P3/5N2/PPPP1PPP/RNBQR1K1 w kq -";
    expect(normaliseFen(input)).toBe(expected);
  });

  it("keeps valid en-passant", () => {
    const input =
      "rnbqkbnr/ppp2ppp/4p3/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3";
    const expected =
      "rnbqkbnr/ppp2ppp/4p3/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6";
    expect(normaliseFen(input)).toBe(expected);
  });

  it("keeps invalid square unchanged", () => {
    const input = "8/8/8/8/8/8/8/8 w KQkq a4 3 7";
    const expected = "8/8/8/8/8/8/8/8 w KQkq a4";
    expect(normaliseFen(input)).toBe(expected);
  });

  it("edge file en-passant white a-file", () => {
    const input = "8/8/8/1P6/8/8/8/8 w - a6 0 1";
    const expected = "8/8/8/1P6/8/8/8/8 w - a6";
    expect(normaliseFen(input)).toBe(expected);
  });

  it("edge file en-passant white no pawn", () => {
    const input = "8/8/8/8/8/8/8/8 w - a6 0 1";
    const expected = "8/8/8/8/8/8/8/8 w - -";
    expect(normaliseFen(input)).toBe(expected);
  });
});
