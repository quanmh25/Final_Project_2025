from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

from models.todo_screen import TodoScreen
from models.category import CategoryScreen
from models.deadline import DeadlineScreen
from models.custom_ui import UIConfig, ModernButton
from models.stats_screen import StatsScreen
from models.database import TodoDB



# =============================================================================
# MAIN APPLICATION
# =============================================================================

class MainApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_listeners = []  # List of widgets that need theme updates

    def create_icon_button(self, text, icon_source, button_type='primary'):
        """Helper method to create button with icon (placed in MainApp class)"""
        btn = ModernButton(button_type=button_type)
        btn.text = ""  # Clear default text
        
        content = BoxLayout(orientation='horizontal', spacing=5)
        
        icon = Image(
            source=icon_source,
            size_hint=(None, None),
            size=(24, 24)
        )
        
        label = Label(
            text=text,
            font_size=UIConfig.BODY_FONT_SIZE,
            color=UIConfig.get_color('TEXT_COLOR')
        )
        
        content.add_widget(icon)
        content.add_widget(label)
        btn.add_widget(content)
        
        return btn

    def build(self):
        self.size = (360, 640)  # Window size
        self.title = "Todo App - Task Management"
        
        UIConfig.load_theme()  # Load saved theme
        
        try:
            self.db = TodoDB()  # Initialize database
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            return Label(text="Database initialization error!")
        
        self.sm = ScreenManager()
        
        # Create todo screen
        self.todo_screen = Screen(name='todo')
        self.todo_widget = TodoScreen(self.db)
        self.todo_screen.add_widget(self.todo_widget)
        self.sm.add_widget(self.todo_screen)
        self.theme_listeners.append(self.todo_widget)
        
        # Create stats screen
        self.stats_screen = Screen(name='stats')
        self.sm.add_widget(self.stats_screen)
        
        # Create category screen
        self.category_screen = Screen(name='categories')
        self.category_screen.add_widget(CategoryScreen(self.db))
        self.sm.add_widget(self.category_screen)
        self.theme_listeners.append(self.category_screen.children[0])

        # Create deadline screen
        self.deadline_screen = Screen(name='deadlines')
        self.deadline_screen.add_widget(DeadlineScreen(self.db))
        self.sm.add_widget(self.deadline_screen)
        self.theme_listeners.append(self.deadline_screen.children[0])
        
        # Main container - child widgets will be arranged vertically (top to bottom)
        root = BoxLayout(orientation='vertical')
        root.add_widget(self.sm)
        
        # Navigation bar
        nav_buttons = BoxLayout(size_hint_y=None, height=60, spacing=5, padding=5)
        
        # Draw background for navigation bar
        with nav_buttons.canvas.before:
            Color(*UIConfig.get_color('SURFACE_COLOR'))
            nav_buttons.bg = Rectangle(pos=nav_buttons.pos, size=nav_buttons.size)
        nav_buttons.bind(pos=lambda w, *args: setattr(w.bg, 'pos', w.pos),
                        size=lambda w, *args: setattr(w.bg, 'size', w.size))
        
        # Navigation buttons
        self.todo_btn = ModernButton(text="Tasks", button_type='primary', color=(1, 1, 1, 1))
        self.todo_btn.bind(on_press=lambda _: setattr(self.sm, 'current', 'todo'))
        
        self.stats_btn = ModernButton(text="Statistics", button_type='secondary', color=(1, 1, 1, 1))
        self.stats_btn.bind(on_press=lambda _: self.switch_to_stats())
        
        self.category_btn = ModernButton(text="Category", button_type='success', color=(1, 1, 1, 1))
        self.category_btn.bind(on_press=lambda _: setattr(self.sm, 'current', 'categories'))
        
        self.deadline_btn = ModernButton(text="Deadline", button_type='warning', color=(1, 1, 1, 1))
        self.deadline_btn.bind(on_press=lambda _: self.switch_to_deadlines())
        
        # Dark/Light theme toggle button
        self.theme_btn = ModernButton(
            text="D" if UIConfig.current_theme == 'light' else "L", 
            button_type='secondary', 
            size_hint_x=None, 
            width=50
        )
        self.theme_btn.bind(on_press=self.toggle_theme)
        
        nav_buttons.add_widget(self.todo_btn)
        nav_buttons.add_widget(self.stats_btn)
        nav_buttons.add_widget(self.category_btn)
        nav_buttons.add_widget(self.deadline_btn)
        nav_buttons.add_widget(self.theme_btn)
        
        root.add_widget(nav_buttons)
        return root

    def toggle_theme(self, instance):
        """Toggle between light and dark theme"""
        new_theme = 'dark' if UIConfig.current_theme == 'light' else 'light'
        UIConfig.set_theme(new_theme)
        instance.text = "D" if new_theme == 'light' else "L"

        # Update theme for all screens
        for listener in self.theme_listeners:
            if hasattr(listener, 'update_theme'):  
                listener.update_theme()

        # Ensure that text color in navigation buttons remains white in any theme
        def fix_nav_colors(dt):
            self.todo_btn.color = (1, 1, 1, 1)
            self.stats_btn.color = (1, 1, 1, 1)
            self.category_btn.color = (1, 1, 1, 1)
            self.deadline_btn.color = (1, 1, 1, 1)
            self.theme_btn.color = (1, 1, 1, 1)
        
        Clock.schedule_once(fix_nav_colors, 0.1)

    def switch_to_stats(self):
        """Switch to statistics screen with refresh"""
        if 'stats' in [screen.name for screen in self.sm.screens]:
            self.sm.remove_widget(self.stats_screen)
        
        self.stats_screen = Screen(name='stats')
        self.stats_widget = StatsScreen(self.db)
        self.stats_screen.add_widget(self.stats_widget)
        self.sm.add_widget(self.stats_screen)
        self.theme_listeners.append(self.stats_widget)
        self.sm.current = 'stats'

    def switch_to_categories(self):
        """Switch to categories screen with refresh"""
        if 'categories' in [screen.name for screen in self.sm.screens]:
            self.sm.remove_widget(self.category_screen)
        
        self.category_screen = Screen(name='categories')
        self.category_screen.add_widget(CategoryScreen(self.db))
        self.sm.add_widget(self.category_screen)
        self.theme_listeners.append(self.category_screen.children[0])
        self.sm.current = 'categories'

    def switch_to_deadlines(self):
        """Switch to deadlines screen with refresh"""
        if 'deadlines' in [screen.name for screen in self.sm.screens]:
            self.sm.remove_widget(self.deadline_screen)
        
        self.deadline_screen = Screen(name='deadlines')
        self.deadline_screen.add_widget(DeadlineScreen(self.db))
        self.sm.add_widget(self.deadline_screen)
        self.theme_listeners.append(self.deadline_screen.children[0])
        self.sm.current = 'deadlines'

    def on_stop(self):
        """Clean up when app is closed"""
        if hasattr(self, 'db'):
            self.db.close()


if __name__ == '__main__':
    MainApp().run()