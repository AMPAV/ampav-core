from importlib.metadata import PackageNotFoundError
import unittest
from unittest.mock import patch

from ampav.core.versioning import package_version


class PackageVersionTest(unittest.TestCase):
    @patch("ampav.core.versioning.version", return_value="1.2.3")
    def test_returns_installed_distribution_version(self, mock_version):
        self.assertEqual(package_version("example-package"), "1.2.3")
        mock_version.assert_called_once_with("example-package")

    @patch(
        "ampav.core.versioning.version",
        side_effect=PackageNotFoundError,
    )
    def test_returns_fallback_when_distribution_is_not_installed(self, mock_version):
        self.assertEqual(package_version("missing-package"), "0+unknown")
        self.assertEqual(
            package_version("missing-package", fallback="development"),
            "development",
        )
        self.assertEqual(mock_version.call_count, 2)


if __name__ == "__main__":
    unittest.main()
