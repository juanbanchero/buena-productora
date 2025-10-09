"""
BuenaLive Auto-Updater Module

This module handles automatic application updates using the tufup framework.
It provides secure, cryptographically-signed updates with support for incremental patches.

Key features:
    - Check for new versions from update repository
    - Download updates securely with TUF (The Update Framework)
    - Apply updates and restart application
    - Support for full archives and incremental patches

Integration with main application:
    - Call check_for_updates() to verify if new version exists
    - Call download_and_install_update() to apply updates
    - Restart application after update completes

See Also:
    - version.py: Application version information
    - build_scripts/: Scripts for building and publishing updates
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple
from packaging import version as pkg_version

from tufup.client import Client
from version import __version__

logger = logging.getLogger(__name__)

# Configuration
APP_NAME = "TicketeraBuena"
UPDATE_REPO_URL = os.getenv(
    "BUENA_LIVE_UPDATE_URL",
    "https://github.com/YOUR_USERNAME/buena-live-updates/raw/main"
)

class UpdaterError(Exception):
    """Base exception for updater-related errors."""
    pass

class BuenaLiveUpdater:
    """
    Manages application updates using tufup framework.

    Attributes:
        current_version (str): Currently installed application version
        client (Client): Tufup client instance for update operations
        app_install_dir (Path): Root directory of installed application
        update_cache_dir (Path): Directory for storing downloaded updates
    """

    def __init__(self):
        """Initialize the updater with current version and paths."""
        self.current_version = __version__
        self.app_install_dir = self._get_install_dir()
        self.update_cache_dir = self.app_install_dir / "updates_cache"
        self.update_cache_dir.mkdir(exist_ok=True)

        # Initialize tufup client
        try:
            self.client = Client(
                app_name=APP_NAME,
                app_install_dir=self.app_install_dir,
                current_version=self.current_version,
                metadata_base_url=f"{UPDATE_REPO_URL}/metadata",
                target_base_url=f"{UPDATE_REPO_URL}/targets",
                refresh_required=False
            )
        except Exception as e:
            logger.error(f"Failed to initialize updater client: {e}")
            raise UpdaterError(f"Could not initialize updater: {e}")

    def _get_install_dir(self) -> Path:
        """
        Determine application installation directory.

        Returns:
            Path: Installation directory path

        Notes:
            - For frozen apps (PyInstaller), uses sys._MEIPASS parent
            - For development, uses current working directory
        """
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return Path(sys._MEIPASS).parent
        else:
            # Running in development mode
            return Path.cwd()

    def check_for_updates(self) -> Tuple[bool, Optional[str]]:
        """
        Check if a new version is available.

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
        try:
            logger.info(f"Checking for updates (current version: {self.current_version})")

            # Refresh metadata from server
            self.client.refresh()

            # Get latest version from targets
            latest_version = self._get_latest_version()

            if latest_version is None:
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

    def _get_latest_version(self) -> Optional[str]:
        """
        Extract latest version from TUF targets.

        Returns:
            Optional[str]: Latest version string, or None if not found
        """
        try:
            # Get all target info from TUF metadata
            targets = self.client.trusted_target_metas

            if not targets:
                return None

            # Find latest version (target files are named like "buena-live-1.0.0.tar.gz")
            versions = []
            for target_path in targets.keys():
                # Extract version from filename
                # Expected format: {app_name}-{version}.tar.gz or .zip
                parts = Path(target_path).stem.split('-')
                if len(parts) >= 2:
                    version_str = parts[-1]
                    try:
                        versions.append(pkg_version.parse(version_str))
                    except pkg_version.InvalidVersion:
                        continue

            if versions:
                return str(max(versions))
            return None

        except Exception as e:
            logger.error(f"Error getting latest version: {e}")
            return None

    def download_and_install_update(self, progress_callback=None) -> bool:
        """
        Download and install available update.

        Args:
            progress_callback (callable, optional): Function called with download progress
                Signature: callback(bytes_downloaded, total_bytes, status_message)

        Returns:
            bool: True if update installed successfully, False otherwise

        Notes:
            - Downloads update to cache directory
            - Applies patches if available (more efficient than full download)
            - Requires application restart to complete update

        Examples:
            >>> def progress(downloaded, total, message):
            ...     print(f"{message}: {downloaded}/{total} bytes")
            >>> updater = BuenaLiveUpdater()
            >>> if updater.download_and_install_update(progress):
            ...     print("Update installed, restart required")
        """
        try:
            logger.info("Starting update download and installation")

            # Check if update is available first
            update_available, latest_version = self.check_for_updates()
            if not update_available:
                logger.info("No update available")
                return False

            # Download the update (tufup handles patch vs full archive automatically)
            if progress_callback:
                progress_callback(0, 100, f"Downloading update {latest_version}")

            # Download targets
            self.client.download_updates()

            if progress_callback:
                progress_callback(50, 100, "Applying update")

            # Apply the update
            self.client.apply_updates()

            if progress_callback:
                progress_callback(100, 100, "Update installed successfully")

            logger.info(f"Update to version {latest_version} installed successfully")
            return True

        except Exception as e:
            logger.error(f"Error during update installation: {e}")
            if progress_callback:
                progress_callback(0, 0, f"Update failed: {str(e)}")
            return False

    def restart_application(self):
        """
        Restart the application to complete update.

        Notes:
            - Closes current process and starts new one
            - Use after successful update installation
        """
        try:
            logger.info("Restarting application")
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except Exception as e:
            logger.error(f"Error restarting application: {e}")
            raise UpdaterError(f"Could not restart application: {e}")


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


def download_and_install_update(progress_callback=None) -> bool:
    """
    Convenience function to download and install update.

    Args:
        progress_callback: Optional progress callback function

    Returns:
        bool: True if update successful
    """
    try:
        updater = BuenaLiveUpdater()
        return updater.download_and_install_update(progress_callback)
    except Exception as e:
        logger.error(f"Error installing update: {e}")
        return False


if __name__ == "__main__":
    # Test updater functionality
    logging.basicConfig(level=logging.INFO)

    print(f"Current version: {__version__}")
    print(f"Checking for updates...")

    available, latest = check_for_updates()
    if available:
        print(f"Update available: {latest}")
    else:
        print("No updates available")
