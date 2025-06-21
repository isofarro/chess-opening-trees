import unittest
from opening_tree.service.opening_tree import OpeningTreeService
from opening_tree.repository.database import OpeningTreeRepository

class TestOpeningTreeService(unittest.TestCase):
    def setUp(self):
        # Initialize with in-memory database
        self.repository = OpeningTreeRepository(':memory:')
        self.service = OpeningTreeService(self.repository)

    def test_format_pgn_date(self):
        """Test PGN date format conversion to ISO-8601.

        Test cases cover all documented formats:
        - YYYY.MM.DD -> YYYY-MM-DD
        - YYYY.MM.?? -> YYYY-MM
        - YYYY.??.?? -> YYYY
        - ????.??.?? -> ''
        - Invalid formats -> ''
        """
        test_cases = [
            # Full dates
            ('2024.03.15', '2024-03-15'),
            ('2023.12.31', '2023-12-31'),

            # Partial dates
            ('2024.03.??', '2024-03'),
            ('2024.??.??', '2024'),

            # Unknown dates
            ('????.??.??', ''),

            # Invalid formats
            ('', ''),
            ('2024', ''),
            ('2024.03', ''),
            ('2024.03.15.01', ''),
            ('invalid', ''),
            ('2024-03-15', ''),  # Using wrong separator
        ]

        for input_date, expected in test_cases:
            with self.subTest(input_date=input_date):
                result = self.service._format_pgn_date(input_date)
                self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()