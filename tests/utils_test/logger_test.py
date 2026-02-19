from unittest import TestCase
from unittest.mock import patch
from utils.logger import Logger

class TestLogger(TestCase):
    @patch('builtins.print')
    def test_log_with_extra_fields(self, mock_print):
        Logger.start()
        Logger.log(level="INFO", message="Test log message", extra_fields={"key": "value"})

        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]
        self.assertIn("[INFO +", output)
        self.assertIn("Test log message", output)
        self.assertIn("[Extra fields]:", output)
        self.assertIn("'key': 'value'", output)

    @patch('builtins.print')
    def test_log_without_extra_fields(self, mock_print):
        Logger.start()
        Logger.log(level="ERROR", message="Something went wrong")

        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]
        self.assertIn("[ERROR +", output)
        self.assertIn("Something went wrong", output)
        self.assertNotIn("[Extra fields]:", output)

    @patch('builtins.print')
    def test_log_elapsed_time_format(self, mock_print):
        Logger.start()
        Logger.log(level="WARNING", message="Elapsed check")

        output = mock_print.call_args[0][0]
        self.assertRegex(output, r"\[WARNING \+\d+\.\d{3}s\]")
        