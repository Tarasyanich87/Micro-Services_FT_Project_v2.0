import os
from functools import lru_cache

class FeatureFlags:
    """
    A simple class to manage feature flags from environment variables.
    Uses lru_cache to avoid reading environment variables on every check.
    """

    @lru_cache(maxsize=None)
    def is_enabled(self, flag_name: str, default: bool = False) -> bool:
        """
        Checks if a feature flag is enabled.
        The flag is considered enabled if its environment variable is set to a truthy value
        (e.g., "true", "1", "yes").
        """
        value = os.environ.get(flag_name, "").lower()
        if not value:
            return default
        return value in ["true", "1", "t", "y", "yes"]

    def is_disabled(self, flag_name: str, default: bool = False) -> bool:
        """Checks if a feature flag is explicitly disabled."""
        return not self.is_enabled(flag_name, not default)

# Global instance
feature_flags = FeatureFlags()

# --- Example Usage ---
# from .feature_flags import feature_flags
#
# if feature_flags.is_enabled("SUPER_SECRET_FEATURE"):
#     # do something amazing
# else:
#     # do the old thing
