from unittest import TestCase
from unittest.mock import Mock

from pipe_operator.utils import tap


class TapTestCase(TestCase):
    def test_tap_with_func(self) -> None:
        mock_func = Mock()
        results = tap(4, mock_func)
        self.assertEqual(results, 4)
        mock_func.assert_called_once_with(4)
