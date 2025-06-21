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
