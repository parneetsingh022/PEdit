from dataclasses import dataclass


@dataclass
class DarkTheme:
    """A modern, grayscale dark theme color palette inspired by GitHub."""
    # Core Colors
    COLOR_PRIMARY: str = "#58a6ff"      # A vibrant blue for primary actions
    COLOR_SECONDARY: str = "#56d364"    # A solid green for secondary actions

    # Background & Surface Colors (Grayscale)
    COLOR_BACKGROUND: str = "#0d1117"  # A deep, near-black
    COLOR_SURFACE: str = "#161b22"      # A lighter shade for cards, modals, etc.
    COLOR_BACKGROUND_ALT: str = "#1c2128" # A shade between the main background and surface
    COLOR_SURFACE_LIGHT: str = "#21262d"   # A lighter surface color, useful for hover states
    COLOR_BACKGROUND_DEEP: str = "#010409" # The darkest shade, almost pure black

    # Text Colors
    COLOR_TEXT_PRIMARY: str = "#e6edf3" # A light gray for primary text
    COLOR_TEXT_SECONDARY: str = "#7d8590" # A dimmer gray for subheadings and muted text

    # Utility Colors
    COLOR_BORDER: str = "#30363d"       # For subtle borders and dividers
    
    # State Colors
    COLOR_SUCCESS: str = "#56d364"      # Green for success notifications
    COLOR_WARNING: str = "#e3b341"      # Orange/amber for warnings
    COLOR_ERROR: str = "#f85149"        # A clear red for errors and alerts
    COLOR_INFO: str = "#58a6ff"         # A calm blue for informational messages

color_theme = DarkTheme()