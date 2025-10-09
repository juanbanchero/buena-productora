"""
BuenaLive Auto-Updater Module

This module handles automatic application updates using GitHub Releases API.
It checks for new versions and directs users to download pages.

Key features:
    - Check for new versions from GitHub Releases
    - Open browser to download page for new versions
    - Simple version comparison

Integration with main application:
    - Call check_for_updates() to verify if new version exists
    - Call open_download_page() to open browser to latest release

See Also:
    - version.py: Application version information
"""

import logging
import webbrowser
from typing import Optional, Tuple
from packaging import version as pkg_version

try:
    import requests
except ImportError:
    requests = None

from version import __version__

logger = logging.getLogger(__name__)

# Configuration
APP_NAME = "TicketeraBuena"
GITHUB_REPO = "juanbanchero/buena-productora"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"

class UpdaterError(Exception):
    """Base exception for updater-related errors."""
    pass

class BuenaLiveUpdater:
    """
    Manages application updates using GitHub Releases API.

    Attributes:
        current_version (str): Currently installed application version
    """

    def __init__(self):
        """Initialize the updater with current version."""
        self.current_version = __version__

    def check_for_updates(self) -> Tuple[bool, Optional[str]]:
        """
        Check if a new version is available on GitHub Releases.

        Returns:
            Tuple[bool, Optional[str]]: (update_available, latest_version)
                - update_available: True if newer version exists
                - latest_version: Version string of latest release, or None if error

        Examples:
            >>> updater = BuenaLiveUpdater()
            >>> available, version = updater.check_for_updates()
            >>> if available:
            ...     print(f"Update available: {version}")
        """
        if requests is None:
            logger.error("requests library not available")
            return False, None

        try:
            logger.info(f"Checking for updates (current version: {self.current_version})")

            # Get latest release from GitHub API
            response = requests.get(GITHUB_API_URL, timeout=10)
            response.raise_for_status()

            release_data = response.json()
            latest_version = release_data.get('tag_name', '').lstrip('v')

            if not latest_version:
                logger.warning("Could not determine latest version")
                return False, None

            # Compare versions
            current = pkg_version.parse(self.current_version)
            latest = pkg_version.parse(latest_version)

            if latest > current:
                logger.info(f"Update available: {latest_version}")
                return True, latest_version
            else:
                logger.info("Application is up to date")
                return False, self.current_version

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False, None

    def open_download_page(self) -> bool:
        """
        Open browser to GitHub Releases download page.

        Returns:
            bool: True if browser opened successfully, False otherwise
        """
        try:
            logger.info("Opening download page in browser")
            webbrowser.open(GITHUB_RELEASES_URL)
            return True
        except Exception as e:
            logger.error(f"Error opening download page: {e}")
            return False


# Convenience functions for easy integration

def check_for_updates() -> Tuple[bool, Optional[str]]:
    """
    Convenience function to check for updates.

    Returns:
        Tuple[bool, Optional[str]]: (update_available, latest_version)
    """
    try:
        updater = BuenaLiveUpdater()
        return updater.check_for_updates()
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return False, None


def open_download_page() -> bool:
    """
    Convenience function to open download page in browser.

    Returns:
        bool: True if successful
    """
    try:
        updater = BuenaLiveUpdater()
        return updater.open_download_page()
    except Exception as e:
        logger.error(f"Error opening download page: {e}")
        return False


if __name__ == "__main__":
    # Test updater functionality
    logging.basicConfig(level=logging.INFO)

    print(f"Current version: {__version__}")
    print(f"Checking for updates...")

    available, latest = check_for_updates()
    if available:
        print(f"Update available: {latest}")
        print("Opening download page...")
        open_download_page()
    else:
        print("No updates available")
