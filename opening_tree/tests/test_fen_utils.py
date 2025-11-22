import unittest
from opening_tree.service.fen_utils import normalise_fen

class TestFenUtils(unittest.TestCase):
    def test_normalise_fen(self):
        """Test FEN normalization by removing move counters and handling en-passant squares."""
        # Test case 1: Basic FEN normalization - removing move counters
        test_fen1 = "r1bq1rk1/2p1bppp/p1np1n2/1p2p3/4P3/1BP2N1P/PP1P1PP1/RNBQR1K1 b - - 0 9"
        expected_fen1 = "r1bq1rk1/2p1bppp/p1np1n2/1p2p3/4P3/1BP2N1P/PP1P1PP1/RNBQR1K1 b - -"
        self.assertEqual(normalise_fen(test_fen1), expected_fen1)

        # Test case 2: Reset en-passant when no valid en-passant capture is possible
        test_fen2 = "r1bqk2r/2ppbppp/p1n2n2/1p2p3/B3P3/5N2/PPPP1PPP/RNBQR1K1 w kq b6 0 7"
        expected_fen2 = "r1bqk2r/2ppbppp/p1n2n2/1p2p3/B3P3/5N2/PPPP1PPP/RNBQR1K1 w kq -"
        self.assertEqual(normalise_fen(test_fen2), expected_fen2)

        # Test case 3: Keep en-passant when a valid en-passant capture is possible
        test_fen3 = "rnbqkbnr/ppp2ppp/4p3/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"
        expected_fen3 = "rnbqkbnr/ppp2ppp/4p3/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6"
        self.assertEqual(normalise_fen(test_fen3), expected_fen3)

    def test_invalid_fen_parts_raises(self):
        with self.assertRaises(ValueError):
            normalise_fen("invalid")

    def test_whitespace_and_segments_trim(self):
        fen = " 8/8/8/8/8/8/8/8   w   KQkq   -   0 1  "
        expected = "8/8/8/8/8/8/8/8 w KQkq -"
        self.assertEqual(normalise_fen(fen), expected)

    def test_invalid_en_passant_square_kept(self):
        fen = "8/8/8/8/8/8/8/8 w KQkq a4 3 7"
        expected = "8/8/8/8/8/8/8/8 w KQkq a4"
        self.assertEqual(normalise_fen(fen), expected)

    def test_white_to_move_en_passant_valid_left(self):
        fen = "8/8/8/2P5/8/8/8/8 w - d6 0 1"
        expected = "8/8/8/2P5/8/8/8/8 w - d6"
        self.assertEqual(normalise_fen(fen), expected)

    def test_white_to_move_en_passant_invalid(self):
        fen = "8/8/8/8/8/8/8/8 w - d6 0 1"
        expected = "8/8/8/8/8/8/8/8 w - -"
        self.assertEqual(normalise_fen(fen), expected)

    def test_black_to_move_en_passant_valid_right(self):
        fen = "8/8/8/8/3p1p2/8/8/8 b - e3 0 1"
        expected = "8/8/8/8/3p1p2/8/8/8 b - e3"
        self.assertEqual(normalise_fen(fen), expected)

    def test_edge_file_en_passant_white_a_file(self):
        fen = "8/8/8/1P6/8/8/8/8 w - a6 0 1"
        expected = "8/8/8/1P6/8/8/8/8 w - a6"
        self.assertEqual(normalise_fen(fen), expected)

    def test_edge_file_en_passant_white_no_pawn(self):
        fen = "8/8/8/8/8/8/8/8 w - a6 0 1"
        expected = "8/8/8/8/8/8/8/8 w - -"
        self.assertEqual(normalise_fen(fen), expected)
