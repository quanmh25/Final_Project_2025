import os
import json
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup


# =============================================================================
# UI DESIGN CONFIGURATION
# =============================================================================

class UIConfig:
    # Light Theme Colors
    LIGHT_THEME = {
        'PRIMARY_COLOR': (0.2, 0.6, 0.9, 1),            # Blue
        'SECONDARY_COLOR': (0.1, 0.4, 0.7, 1),          # Dark Blue
        'SUCCESS_COLOR': (0.2, 0.8, 0.4, 1),            # Green
        'WARNING_COLOR': (1, 0.6, 0.2, 1),              # Orange
        'DANGER_COLOR': (0.9, 0.3, 0.3, 1),             # Red
        'BACKGROUND_COLOR': (0.95, 0.95, 0.97, 1),      # Light Gray
        'SURFACE_COLOR': (1, 1, 1, 1),                  # White
        'TEXT_COLOR': (0, 0, 0, 1),                     # Black
        'DISABLED_COLOR': (0.7, 0.7, 0.7, 1),           # Gray
    }

    # Dark Theme Colors
    DARK_THEME = {
        'PRIMARY_COLOR': (0.3, 0.7, 1.0, 1),            # Lighter Blue
        'SECONDARY_COLOR': (0.2, 0.5, 0.8, 1),          # Slightly Lighter Dark Blue
        'SUCCESS_COLOR': (0.3, 0.9, 0.5, 1),            # Brighter Green
        'WARNING_COLOR': (1, 0.7, 0.3, 1),              # Brighter Orange
        'DANGER_COLOR': (1.0, 0.4, 0.4, 1),             # Brighter Red
        'BACKGROUND_COLOR': (0.1, 0.1, 0.15, 1),        # Dark Gray
        'SURFACE_COLOR': (0.2, 0.2, 0.25, 1),           # Darker Gray
        'TEXT_COLOR': (1, 1, 1, 1),                     # White (increased contrast)
        'DISABLED_COLOR': (0.5, 0.5, 0.5, 1),           # Medium Gray
    }

    # Current theme configuration
    current_theme = 'light'
    theme_data = LIGHT_THEME

    # UI Dimensions
    BUTTON_HEIGHT = 48              # Button height
    INPUT_HEIGHT = 48               # Input field height
    TASK_HEIGHT = 60                # Task item height
    BORDER_RADIUS = 12              # Corner radius
    PADDING = 16                    # Padding spacing
    SPACING = 12                    # Widget spacing

    # Typography Settings
    TITLE_FONT_SIZE = 20
    SUBTITLE_FONT_SIZE = 16
    BODY_FONT_SIZE = 14
    CAPTION_FONT_SIZE = 12

    @staticmethod
    def set_theme(theme_name):
        """Set the current theme and update theme_data."""
        if theme_name not in ['light', 'dark']:
            theme_name = 'light'
        UIConfig.current_theme = theme_name
        UIConfig.theme_data = UIConfig.DARK_THEME if theme_name == 'dark' else UIConfig.LIGHT_THEME
        
        # Save theme to file
        try:
            with open('data/theme.json', 'w') as f:
                json.dump({'theme': theme_name}, f)
        except Exception as e:
            print(f"Error saving theme: {e}")

    @staticmethod
    def load_theme():
        """Load the saved theme from file."""
        try:
            if os.path.exists('data/theme.json'):
                with open('data/theme.json', 'r') as f:
                    data = json.load(f)
                    UIConfig.set_theme(data.get('theme', 'light'))
        except Exception as e:
            print(f"Error loading theme: {e}")
            UIConfig.set_theme('light')

    @staticmethod
    def get_color(color_name):
        """Get color based on current theme."""
        return UIConfig.theme_data.get(color_name, (1, 1, 1, 1))


# =============================================================================
# CUSTOM UI COMPONENTS
# =============================================================================

class ModernButton(Button):
    """Modern styled button with theme support."""
    
    def __init__(self, button_type='primary', **kwargs):
        super().__init__(**kwargs)
        self.button_type = button_type
        self.size_hint_y = None                         # Don't auto-adjust height
        self.height = UIConfig.BUTTON_HEIGHT
        self.font_size = UIConfig.BODY_FONT_SIZE
        self.bold = True
        self.update_colors()
        self.color = (1, 1, 1, 1)                       # Set white text color

    def update_colors(self):
        """Update button colors based on theme and button type."""
        color_map = {
            'primary': UIConfig.get_color('PRIMARY_COLOR'),
            'secondary': UIConfig.get_color('SECONDARY_COLOR'),
            'success': UIConfig.get_color('SUCCESS_COLOR'),
            'danger': UIConfig.get_color('DANGER_COLOR')
        }
        # Get background color based on button type
        self.background_color = color_map.get(self.button_type, UIConfig.get_color('PRIMARY_COLOR'))
        # Schedule text color setting after 1 frame
        Clock.schedule_once(lambda dt: setattr(self, 'color', (1, 1, 1, 1)), 0)


class ModernTextInput(TextInput):
    """Modern styled text input with theme support."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = UIConfig.INPUT_HEIGHT
        self.font_size = UIConfig.BODY_FONT_SIZE
        self.background_color = UIConfig.get_color('SURFACE_COLOR')
        self.foreground_color = UIConfig.get_color('TEXT_COLOR')
        self.padding = [UIConfig.PADDING//2, UIConfig.PADDING//2]


# =============================================================================
# DIALOG COMPONENTS
# =============================================================================

class ConfirmDialog(Popup):
    """Confirmation dialog popup."""
    
    def __init__(self, message, callback, **kwargs):
        super().__init__(**kwargs)
        self.title = "Confirm"
        self.size_hint = (0.8, 0.4)
        self.callback = callback
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        content.add_widget(Label(
            text=message,
            text_size=(None, None),
            color=(1, 1, 1, 1)  # Always show white text regardless of theme
        ))
        
        buttons = BoxLayout(spacing=10, size_hint_y=None, height=40)
        
        yes_btn = ModernButton(text="Yes", button_type='success')
        yes_btn.bind(on_press=self.on_yes)
        
        no_btn = ModernButton(text="No", button_type='secondary')
        no_btn.bind(on_press=self.on_no)
        
        buttons.add_widget(yes_btn)
        buttons.add_widget(no_btn)
        
        content.add_widget(buttons)
        self.content = content

    def on_yes(self, instance):
        """Handle Yes button press."""
        self.callback()
        self.dismiss()

    def on_no(self, instance):
        """Handle No button press."""
        self.dismiss()