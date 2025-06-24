import sqlite3
import json
import os
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.widget import Widget


class UIConfig(EventDispatcher):
    theme_changed = ObjectProperty(None, allownone=True)
    
    # Themes
    LIGHT_THEME = {
        'PRIMARY_COLOR': (0.2, 0.6, 0.9, 1),      # Blue
        'SECONDARY_COLOR': (0.1, 0.4, 0.7, 1),    # Dark Blue
        'SUCCESS_COLOR': (0.2, 0.8, 0.4, 1),      # Green
        'WARNING_COLOR': (1, 0.6, 0.2, 1),        # Orange
        'DANGER_COLOR': (0.9, 0.3, 0.3, 1),       # Red
        'BACKGROUND_COLOR': (0.95, 0.95, 0.97, 1),# Light Gray
        'SURFACE_COLOR': (1, 1, 1, 1),            # White
        'TEXT_COLOR': (0, 0, 0, 1),               # Black
        'DISABLED_COLOR': (0.7, 0.7, 0.7, 1),     # Gray
    }

    DARK_THEME = {
        'PRIMARY_COLOR': (0.3, 0.7, 1.0, 1),      # Lighter Blue
        'SECONDARY_COLOR': (0.2, 0.5, 0.8, 1),    # Slightly Lighter Dark Blue
        'SUCCESS_COLOR': (0.3, 0.9, 0.5, 1),      # Brighter Green
        'WARNING_COLOR': (1, 0.7, 0.3, 1),        # Brighter Orange
        'DANGER_COLOR': (1.0, 0.4, 0.4, 1),       # Brighter Red
        'BACKGROUND_COLOR': (0.1, 0.1, 0.15, 1),  # Dark Gray
        'SURFACE_COLOR': (0.2, 0.2, 0.25, 1),     # Darker Gray
        'TEXT_COLOR': (1, 1, 1, 1),               # White (increased contrast)
        'DISABLED_COLOR': (0.5, 0.5, 0.5, 1),     # Medium Gray
    }

    # Current theme
    current_theme = 'light'
    theme_data = LIGHT_THEME.copy()

    # Sizes
    BUTTON_HEIGHT = 48
    INPUT_HEIGHT = 48
    TASK_HEIGHT = 60
    BORDER_RADIUS = 12
    PADDING = 16
    SPACING = 12

    # Typography
    TITLE_FONT_SIZE = 20
    SUBTITLE_FONT_SIZE = 16
    BODY_FONT_SIZE = 14
    CAPTION_FONT_SIZE = 12

    # Singleton instance
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UIConfig, cls).__new__(cls)
        return cls._instance

    @classmethod
    def set_theme(cls, theme_name):
        """Set the current theme and update theme_data."""
        if theme_name not in ['light', 'dark']:
            theme_name = 'light'
        
        cls.current_theme = theme_name
        cls.theme_data = cls.DARK_THEME.copy() if theme_name == 'dark' else cls.LIGHT_THEME.copy()

        if cls._instance:
            cls._instance.dispatch('on_theme_changed', theme_name)  # ← Thêm dispatch
            cls._instance.theme_changed = theme_name

        # Save theme to file
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/theme.json', 'w') as f:
                json.dump({'theme': theme_name}, f)
        except Exception as e:
            print(f"Error saving theme: {e}")

    @classmethod
    def load_theme(cls):
        """Load the saved theme from file."""
        try:
            if os.path.exists('data/theme.json'):
                with open('data/theme.json', 'r') as f:
                    data = json.load(f)
                    cls.set_theme(data.get('theme', 'light'))
            else:
                cls.set_theme('light')
        except Exception as e:
            print(f"Error loading theme: {e}")
            cls.set_theme('light')

    @classmethod
    def get_color(cls, color_name):
        """Get color based on current theme."""
        return cls.theme_data.get(color_name, (1, 1, 1, 1))
    
    def on_theme_changed(self, theme_name):
        pass  # Event handler placeholder


class CategoryDB:
    def __init__(self, db_path="data/todo.db"):
        os.makedirs('data', exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.create_category_tables()
    
    def create_category_tables(self):
        try:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS categories
                                 (id INTEGER PRIMARY KEY,
                                  name TEXT UNIQUE NOT NULL,
                                  icon TEXT DEFAULT 'Default',
                                  color TEXT DEFAULT '#4CAF50',
                                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            try:
                self.conn.execute('ALTER TABLE tasks ADD COLUMN category_id INTEGER')
                self.conn.execute('ALTER TABLE tasks ADD COLUMN tags TEXT')
            except sqlite3.OperationalError:
                pass
            default_categories = [
                ('Work', 'Work', '#2196F3'),
                ('Personal', 'Personal', '#4CAF50'), 
                ('Study', 'Study', '#FF9800'),
                ('Health', 'Health', '#F44336'),
                ('Shopping', 'Shopping', '#9C27B0'),
                ('Home', 'Home', '#795548')
            ]
            for name, icon, color in default_categories:
                try:
                    self.conn.execute('INSERT INTO categories (name, icon, color) VALUES (?, ?, ?)',
                                    (name, icon, color))
                except sqlite3.IntegrityError:
                    pass
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating category tables: {e}")
    
    def add_category(self, name, icon='Default', color='#4CAF50'):
        try:
            self.conn.execute('INSERT INTO categories (name, icon, color) VALUES (?, ?, ?)',
                            (name, icon, color))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding category: {e}")
            return False
    
    def get_categories(self):
        try:
            cursor = self.conn.execute('SELECT id, name, icon, color FROM categories ORDER BY name')
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting categories: {e}")
            return []
    
    def delete_category(self, category_id):
        try:
            self.conn.execute('UPDATE tasks SET category_id = NULL WHERE category_id = ?', 
                            (category_id,))
            self.conn.execute('DELETE FROM categories WHERE id = ?', (category_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting category: {e}")
            return False
    
    def set_task_category(self, task_id, category_id):
        try:
            self.conn.execute('UPDATE tasks SET category_id = ? WHERE id = ?',
                            (category_id, task_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error setting task category: {e}")
            return False
    
    def get_tasks_by_category(self, category_id=None):
        try:
            if category_id:
                cursor = self.conn.execute('''SELECT t.id, t.title, t.done, c.name, c.icon
                                            FROM tasks t
                                            LEFT JOIN categories c ON t.category_id = c.id
                                            WHERE t.category_id = ?
                                            ORDER BY t.done ASC, t.id DESC''', (category_id,))
            else:
                cursor = self.conn.execute('''SELECT t.id, t.title, t.done, c.name, c.icon
                                            FROM tasks t
                                            LEFT JOIN categories c ON t.category_id = c.id
                                            ORDER BY c.name, t.done ASC, t.id DESC''')
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting tasks by category: {e}")
            return []
    
    def get_category_stats(self):
        try:
            cursor = self.conn.execute('''SELECT c.id, c.name, c.icon, 
                                        COUNT(t.id) as total_tasks,
                                        SUM(CASE WHEN t.done = 1 THEN 1 ELSE 0 END) as completed_tasks
                                        FROM categories c
                                        LEFT JOIN tasks t ON c.id = t.category_id
                                        GROUP BY c.id, c.name, c.icon
                                        ORDER BY total_tasks DESC''')
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting category stats: {e}")
            return []
    
    def add_tag_to_task(self, task_id, tags):
        try:
            tag_str = ','.join(tags) if isinstance(tags, list) else tags
            self.conn.execute('UPDATE tasks SET tags = ? WHERE id = ?',
                            (tag_str, task_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding tags: {e}")
            return False
    
    def get_all_tags(self):
        try:
            cursor = self.conn.execute('SELECT DISTINCT tags FROM tasks WHERE tags IS NOT NULL AND tags != ""')
            all_tags = set()
            for row in cursor.fetchall():
                if row[0]:
                    all_tags.update(tag.strip() for tag in row[0].split(','))
            return sorted(list(all_tags))
        except sqlite3.Error as e:
            print(f"Error getting tags: {e}")
            return []
    
    def search_tasks_by_tag(self, tag):
        try:
            cursor = self.conn.execute('''SELECT t.id, t.title, t.done, c.name, c.icon, t.tags
                                        FROM tasks t
                                        LEFT JOIN categories c ON t.category_id = c.id
                                        WHERE t.tags LIKE ?
                                        ORDER BY t.done ASC, t.id DESC''', (f'%{tag}%',))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error searching tasks by tag: {e}")
            return []


class CategoryPopup(Popup):
    def __init__(self, category_db, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.category_db = category_db
        self.callback = callback
        
        self.title = "Add New Category"
        self.size_hint = (0.8, 0.6)
        
        self.build_content()
        self.apply_theme()
        
        # Bind theme change
        UIConfig().bind(theme_changed=self.on_theme_changed)
    
    def build_content(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        name_label = Label(text="Category Name:", size_hint_y=None, height=30)
        content.add_widget(name_label)
        
        self.name_input = TextInput(size_hint_y=None, height=40, multiline=False)
        content.add_widget(self.name_input)
        
        icon_label = Label(text="Icon (text):", size_hint_y=None, height=30)
        content.add_widget(icon_label)
        
        self.icon_input = TextInput(text="Default", size_hint_y=None, height=40, multiline=False)
        content.add_widget(self.icon_input)
        
        color_label = Label(text="Color (hex code):", size_hint_y=None, height=30)
        content.add_widget(color_label)
        
        self.color_input = TextInput(text="#4CAF50", size_hint_y=None, height=40, multiline=False)
        content.add_widget(self.color_input)
        
        buttons = BoxLayout(spacing=10, size_hint_y=None, height=50)
        
        self.save_btn = Button(text="Save")
        self.save_btn.bind(on_press=self.save_category)
        
        self.cancel_btn = Button(text="Cancel")
        self.cancel_btn.bind(on_press=self.dismiss)
        
        buttons.add_widget(self.save_btn)
        buttons.add_widget(self.cancel_btn)
        content.add_widget(buttons)
        
        # Store references to labels for theme updates
        self.name_label = name_label
        self.icon_label = icon_label
        self.color_label = color_label
        
        self.content = content
    
    def on_theme_changed(self, instance, value):
        self.apply_theme()
    
    def apply_theme(self):
        self.background_color = UIConfig.get_color('SURFACE_COLOR')
        
        # Apply theme to labels
        self.name_label.color = UIConfig.get_color('TEXT_COLOR')
        self.icon_label.color = UIConfig.get_color('TEXT_COLOR')
        self.color_label.color = UIConfig.get_color('TEXT_COLOR')
        
        # Apply theme to buttons
        self.apply_button_theme(self.save_btn, 'PRIMARY_COLOR')
        self.apply_button_theme(self.cancel_btn, 'DISABLED_COLOR')
        
        # Apply theme to inputs
        self.apply_input_theme(self.name_input)
        self.apply_input_theme(self.icon_input)
        self.apply_input_theme(self.color_input)
        
    def apply_button_theme(self, button, color_key):
        button.background_color = UIConfig.get_color(color_key)
        button.color = UIConfig.get_color('TEXT_COLOR')
        
    def apply_input_theme(self, text_input):
        text_input.background_color = UIConfig.get_color('SURFACE_COLOR')
        text_input.foreground_color = UIConfig.get_color('TEXT_COLOR')
    
    def save_category(self, instance):
        name = self.name_input.text.strip()
        icon = self.icon_input.text.strip() or "Default"
        color = self.color_input.text.strip() or "#4CAF50"
        
        if not name:
            self.show_error("Category name is required!")
            return
        
        success = self.category_db.add_category(name, icon, color)
        if success:
            if self.callback:
                self.callback()
            self.dismiss()
        else:
            self.show_error("Error adding category!")
    
    def show_error(self, message):
        error_popup = Popup(
            title="Error",
            content=Label(text=message, color=UIConfig.get_color('TEXT_COLOR')),
            size_hint=(0.6, 0.3),
            background_color=UIConfig.get_color('SURFACE_COLOR')
        )
        error_popup.open()


class TaskCategoryPopup(Popup):
    def __init__(self, task_id, task_title, category_db, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.task_id = task_id
        self.category_db = category_db
        self.callback = callback
        
        self.title = f"Categorize: {task_title}"
        self.size_hint = (0.8, 0.5)
        
        self.build_content()
        self.apply_theme()
        
        # Bind theme change
        UIConfig().bind(theme_changed=self.on_theme_changed)
    
    def build_content(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        category_label = Label(text="Select Category:", size_hint_y=None, height=30)
        content.add_widget(category_label)
        
        categories = self.category_db.get_categories()
        category_options = ["None"] + [name for _, name, _, _ in categories]
        
        self.category_spinner = Spinner(
            text="None",
            values=category_options,
            size_hint_y=None,
            height=40
        )
        content.add_widget(self.category_spinner)
        
        tags_label = Label(text="Tags (comma-separated):", size_hint_y=None, height=30)
        content.add_widget(tags_label)
        
        self.tags_input = TextInput(size_hint_y=None, height=40, multiline=False,
                                  hint_text="work, urgent, meeting")
        content.add_widget(self.tags_input)
        
        buttons = BoxLayout(spacing=10, size_hint_y=None, height=50)
        
        self.save_btn = Button(text="Save")
        self.save_btn.bind(on_press=self.save_categorization)
        
        self.cancel_btn = Button(text="Cancel")
        self.cancel_btn.bind(on_press=self.dismiss)
        
        buttons.add_widget(self.save_btn)
        buttons.add_widget(self.cancel_btn)
        content.add_widget(buttons)
        
        # Store references for theme updates
        self.category_label = category_label
        self.tags_label = tags_label
        self.categories = categories
        
        self.content = content
    
    def on_theme_changed(self, instance, value):
        self.apply_theme()
    
    def apply_theme(self):
        self.background_color = UIConfig.get_color('SURFACE_COLOR')
        
        # Apply theme to labels
        self.category_label.color = UIConfig.get_color('TEXT_COLOR')
        self.tags_label.color = UIConfig.get_color('TEXT_COLOR')
        
        # Apply theme to buttons
        self.apply_button_theme(self.save_btn, 'PRIMARY_COLOR')
        self.apply_button_theme(self.cancel_btn, 'DISABLED_COLOR')
        
        # Apply theme to inputs and spinner
        self.apply_input_theme(self.tags_input)
        self.apply_spinner_theme(self.category_spinner)
        
    def apply_button_theme(self, button, color_key):
        button.background_color = UIConfig.get_color(color_key)
        button.color = UIConfig.get_color('TEXT_COLOR')
        
    def apply_input_theme(self, text_input):
        text_input.background_color = UIConfig.get_color('SURFACE_COLOR')
        text_input.foreground_color = UIConfig.get_color('TEXT_COLOR')
        
    def apply_spinner_theme(self, spinner):
        spinner.background_color = UIConfig.get_color('SURFACE_COLOR')
        spinner.color = UIConfig.get_color('TEXT_COLOR')
    
    def save_categorization(self, instance):
        selected_text = self.category_spinner.text
        category_id = None
        
        if selected_text != "None":
            for cat_id, name, _, _ in self.categories:
                if selected_text == name:
                    category_id = cat_id
                    break
        
        self.category_db.set_task_category(self.task_id, category_id)
        
        tags = self.tags_input.text.strip()
        if tags:
            self.category_db.add_tag_to_task(self.task_id, tags)
        
        if self.callback:
            self.callback()
        self.dismiss()


class CategoryScreen(BoxLayout):
    def __init__(self, main_db, **kwargs):
        super().__init__(**kwargs)
        self.main_db = main_db
        self.category_db = CategoryDB()
        self.orientation = 'vertical'
        self.spacing = 5
        self.padding = 10
        
        UIConfig.load_theme()
        
        self.setup_ui()
        self.apply_theme()
        self.refresh_view()
        
        # Bind theme change
        ui_config = UIConfig()
        ui_config.bind(theme_changed=self.on_theme_changed)

    def on_theme_changed(self, instance, value):
        """Called when theme changes"""
        self.apply_theme()
        self.refresh_view()

    def setup_ui(self):
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10) # Header
        
        self.title_label = Label(text="Categories & Tags", font_size='18sp')
        header.add_widget(self.title_label)
        
        self.add_category_btn = Button(text="Add Category", size_hint_x=None, width=120)
        self.add_category_btn.bind(on_press=lambda x: self.add_category())
        header.add_widget(self.add_category_btn)
        
        self.back_btn = Button(text="Back", size_hint_x=None, width=80)
        self.back_btn.bind(on_press=self.go_back)
        header.add_widget(self.back_btn)
        
        self.add_widget(header)
        
        # Filter section
        filter_section = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        self.filter_label = Label(text="Filter by:", size_hint_x=None, width=80)
        filter_section.add_widget(self.filter_label)
        
        self.filter_spinner = Spinner(
            text='All Categories',
            values=['All Categories'],
            size_hint_x=None,
            width=150
        )
        self.filter_spinner.bind(text=self.on_filter_change)
        filter_section.add_widget(self.filter_spinner)
        
        filter_section.add_widget(Widget()) #đẩy phần sau sang phải
        
        self.tag_label = Label(text="Tag:", size_hint_x=None, width=40)
        filter_section.add_widget(self.tag_label)
        
        self.tag_search = TextInput(hint_text="Search by tag...", 
                                  size_hint_x=None, 
                                  width=150, 
                                  halign='left',
                                  multiline=False,
                                  padding_y=(15, 10)
                                  )
        self.tag_search.bind(on_text_validate=self.search_by_tag)
        filter_section.add_widget(self.tag_search)


        self.search_btn = Button(text="Search", size_hint_x=None, width=80)
        self.search_btn.bind(on_press=lambda x: self.search_by_tag())
        filter_section.add_widget(self.search_btn)
        
        self.add_widget(filter_section)
        
        # Stats container
        self.stats_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.stats_container.bind(minimum_height=self.stats_container.setter('height'))
        self.add_widget(self.stats_container)
        
        # Tasks scroll view
        scroll = ScrollView()
        self.tasks_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.tasks_container.bind(minimum_height=self.tasks_container.setter('height'))
        scroll.add_widget(self.tasks_container)
        self.add_widget(scroll)

    def update_filter_options(self):
        categories = self.category_db.get_categories()
        options = ['All Categories'] + [name for _, name, _, _ in categories]
        self.filter_spinner.values = options

    def apply_theme(self):
        # Clear and redraw background
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*UIConfig.get_color('BACKGROUND_COLOR'))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_background, size=self.update_background)
    
        # Apply theme to labels
        self.title_label.color = UIConfig.get_color('TEXT_COLOR')
        self.filter_label.color = UIConfig.get_color('TEXT_COLOR')
        self.tag_label.color = UIConfig.get_color('TEXT_COLOR')
        
        # Apply theme to buttons
        self.apply_button_theme(self.add_category_btn, 'PRIMARY_COLOR')
        self.apply_button_theme(self.back_btn, 'SECONDARY_COLOR')
        self.apply_button_theme(self.search_btn, 'PRIMARY_COLOR')
        
        # Apply theme to inputs and spinner
        self.apply_input_theme(self.tag_search)
        self.apply_spinner_theme(self.filter_spinner)

    def update_background(self, *args):
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size

    def apply_button_theme(self, button, color_key):
        button.background_color = UIConfig.get_color(color_key)
        button.color = UIConfig.get_color('TEXT_COLOR')
        
    def apply_input_theme(self, text_input):
        text_input.background_color = UIConfig.get_color('SURFACE_COLOR')
        text_input.foreground_color = UIConfig.get_color('TEXT_COLOR')
        
    def apply_spinner_theme(self, spinner):
        spinner.background_color = UIConfig.get_color('SURFACE_COLOR')
        spinner.color = UIConfig.get_color('TEXT_COLOR')

    def go_back(self, instance):
        if hasattr(self, 'manager'):
            self.manager.current = 'tasks'

    def refresh_view(self):
        self.update_filter_options()
        self.update_stats()
        self.refresh_tasks()
    
    def update_filter_options(self):
        categories = self.category_db.get_categories()
        options = ['All Categories'] + [name for _, name, _, _ in categories]
        self.filter_spinner.values = options
    
    def update_stats(self):
        self.stats_container.clear_widgets()
        
        stats = self.category_db.get_category_stats()
        if stats:
            stats_header = Label(text="Category Statistics", 
                               size_hint_y=None, height=30, bold=True, font_size='18sp')
            stats_header.color = UIConfig.get_color('TEXT_COLOR')
            self.stats_container.add_widget(stats_header)
            
            headers_layout = BoxLayout(
                size_hint_y=None,
                height=40,
                spacing=5,
                padding=5
            )
            headers = ["Category", "Total", "Done", "Progress", "Action"]
            header_widths = [160, 170, 160, 160, 100]
            for header, width in zip(headers, header_widths):
                header_label = Label(
                    text=header,
                    size_hint_y=None,
                    height=40,
                    color=UIConfig.get_color('TEXT_COLOR'),
                    bold=True,
                    halign='center',
                    valign='middle',
                    size_hint_x=None,
                    # size=(100, 40)
                    width=width  # Cố định độ rộng để khớp với nội dung
                )
                headers_layout.add_widget(header_label)
            self.stats_container.add_widget(headers_layout)

            for category_id, name, icon, total, completed in stats:
                if total > 0:
                    progress = f"{completed}/{total} ({completed/total*100:.0f}%)"
                    
                    # BoxLayout cho từng hàng, tương tự task_layout
                    stat_row = BoxLayout(
                        size_hint_y=None,
                        height=50,
                        spacing=5,
                        padding=5
                    )
                    
                    # Nhãn danh mục
                    category_label = Label(
                        text=name,
                        size_hint_y=None,
                        height=50,
                        color=UIConfig.get_color('TEXT_COLOR'),
                        halign='center',
                        valign='middle',
                        size=(100, 40)
                    )
                    stat_row.add_widget(category_label)
                    
                    # Nhãn tổng số nhiệm vụ
                    total_label = Label(
                        text=str(total),
                        size_hint_y=None,
                        height=50,
                        color=UIConfig.get_color('TEXT_COLOR'),
                        halign='center',
                        valign='middle',
                        size=(100, 40)
                    )
                    stat_row.add_widget(total_label)
                    
                    # Nhãn nhiệm vụ hoàn thành
                    completed_label = Label(
                        text=str(completed),
                        size_hint_y=None,
                        height=50,
                        color=UIConfig.get_color('TEXT_COLOR'),
                        halign='center',
                        valign='middle',
                        size=(100, 40)
                    )
                    stat_row.add_widget(completed_label)
                    
                    # Nhãn tiến độ
                    progress_label = Label(
                        text=progress,
                        size_hint_y=None,
                        height=50,
                        color=UIConfig.get_color('TEXT_COLOR'),
                        halign='center',
                        valign='middle',
                        size=(100, 40)
                    )
                    stat_row.add_widget(progress_label)
                    
                    delete_btn = Button(
                        text="Delete",
                        size_hint=(None, None),
                        size=(100, 40),  # Khớp với kích thước của Categorize
                        background_color=UIConfig.get_color('DANGER_COLOR'),
                        color=UIConfig.get_color('TEXT_COLOR'),
                        halign='center',
                        valign='middle'
                    )
                    delete_btn.bind(on_press=lambda x, cat_id=category_id, cat_name=name: 
                                self.delete_category(cat_id, cat_name))
                    stat_row.add_widget(delete_btn)
                    
                    self.stats_container.add_widget(stat_row)

    def on_filter_change(self, spinner, text):
        self.refresh_tasks()
    
    def refresh_tasks(self):
        self.tasks_container.clear_widgets()
        
        selected_category = None
        if self.filter_spinner.text != 'All Categories':
            categories = self.category_db.get_categories()
            for cat_id, name, _, _ in categories:
                if self.filter_spinner.text == name:
                    selected_category = cat_id
                    break
        
        tasks = self.category_db.get_tasks_by_category(selected_category)
        
        if not tasks:
            no_tasks_label = Label(
                text="No tasks in this category!",
                size_hint_y=None,
                height=0,
                color=UIConfig.get_color('TEXT_COLOR'),
                halign='center',
                valign='middle',
                pos_hint={'center_y': 0.5}
            )
            self.tasks_container.add_widget(no_tasks_label)
            return

        # Create task list
        for task_id, title, done, category_name, category_icon in tasks:
            task_layout = BoxLayout(
                size_hint_y=None,
                height=70,
                spacing=5,
                padding=5,
                pos_hint={'center_y': 0.5}
            )

            # Task status checkbox
            status_btn = Button(
                text='C' if done else 'P',
                size_hint=(None, None),
                size=(40, 40),
                halign='center',
                valign='middle',
                pos_hint={'center_y': 0.5},
                background_color=UIConfig.get_color('SUCCESS_COLOR' if done else 'PRIMARY_COLOR'),
                color=UIConfig.get_color('TEXT_COLOR')
            )
            status_btn.bind(on_press=lambda x, tid=task_id: self.toggle_task_status(tid))
            task_layout.add_widget(status_btn)

            # Task title and category
            task_info = BoxLayout(orientation='vertical', spacing=2, size_hint_x=1, padding=0)
            title_label = Label(
                text=title,
                size_hint_y=None,
                height=25,
                halign='left',
                color=UIConfig.get_color('TEXT_COLOR'),
                text_size=(self.width - 200, None)
            )
            category_text = f"[{category_name}]" if category_name else "[No Category]"
            category_label = Label(
                text=category_text,
                size_hint_y=None,
                height=20,
                color=UIConfig.get_color('TEXT_COLOR'),
                font_size=12
            )
            task_info.add_widget(title_label)
            task_info.add_widget(category_label)
            task_layout.add_widget(task_info)

            # Categorize button
            categorize_btn = Button(
                text="Categorize",
                size_hint=(None, None),
                size=(100, 40),
                background_color=UIConfig.get_color('SECONDARY_COLOR'),
                color=UIConfig.get_color('TEXT_COLOR')
            )
            categorize_btn.bind(on_press=lambda x, tid=task_id, ttitle=title: 
                              self.open_categorize_popup(tid, ttitle))
            task_layout.add_widget(categorize_btn)

            self.tasks_container.add_widget(task_layout)

    def toggle_task_status(self, task_id):
        """Toggle task completion status"""
        try:
            self.main_db.conn.execute(
                'UPDATE tasks SET done = 1 - done WHERE id = ?',
                (task_id,)
            )
            self.main_db.conn.commit()
            self.refresh_view()
        except sqlite3.Error as e:
            print(f"Error toggling task status: {e}")
            self.show_error("Error updating task status!")

    def add_category(self):
        """Open popup to add new category"""
        popup = CategoryPopup(
            category_db=self.category_db,
            callback=self.refresh_view
        )
        popup.open()

    def open_categorize_popup(self, task_id, task_title):
        """Open popup to categorize a task"""
        popup = TaskCategoryPopup(
            task_id=task_id,
            task_title=task_title,
            category_db=self.category_db,
            callback=self.refresh_view
        )
        popup.open()

    def delete_category(self, category_id, category_name):
        """Delete a category with confirmation"""
        confirm_popup = Popup(
            title=f"Delete {category_name}?",
            size_hint=(0.6, 0.4),
            background_color=UIConfig.get_color('SURFACE_COLOR')
        )
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        warning_label = Label(
            text=f"Are you sure you want to delete '{category_name}'?\nTasks will be uncategorized.",
            color=UIConfig.get_color('TEXT_COLOR'),
            text_size=(300, None)
        )
        content.add_widget(warning_label)

        buttons = BoxLayout(spacing=10, size_hint_y=None, height=50)
        confirm_btn = Button(
            text="Delete",
            background_color=UIConfig.get_color('DANGER_COLOR'),
            color=UIConfig.get_color('TEXT_COLOR')
        )
        confirm_btn.bind(on_press=lambda x: self.confirm_delete(category_id, confirm_popup))
        cancel_btn = Button(
            text="Cancel",
            background_color=UIConfig.get_color('SECONDARY_COLOR'),
            color=UIConfig.get_color('TEXT_COLOR')
        )
        cancel_btn.bind(on_press=confirm_popup.dismiss)
        
        buttons.add_widget(confirm_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        
        confirm_popup.content = content
        confirm_popup.open()

    def confirm_delete(self, category_id, popup):
        """Execute category deletion"""
        success = self.category_db.delete_category(category_id)
        if success:
            self.refresh_view()
            popup.dismiss()
        else:
            popup.dismiss()
            self.show_error("Error deleting category!")

    def search_by_tag(self, instance=None):
        """Search tasks by tag"""
        tag = self.tag_search.text.strip()
        if not tag:
            self.refresh_tasks()
            return

        self.tasks_container.clear_widgets()
        tasks = self.category_db.search_tasks_by_tag(tag)
        
        if not tasks:
            no_tasks_label = Label(
                text=f"No tasks found with tag '{tag}'!",
                size_hint_y=None,
                height=40,
                color=UIConfig.get_color('TEXT_COLOR')
            )
            self.tasks_container.add_widget(no_tasks_label)
            return

        for task_id, title, done, category_name, category_icon, tags in tasks:
            task_layout = BoxLayout(
                size_hint_y=None,
                height=50,
                spacing=5,
                padding=5
            )

            status_btn = Button(
                text='✓' if done else '○',
                size_hint=(None, None),
                size=(40, 40),
                background_color=UIConfig.get_color('SUCCESS_COLOR' if done else 'PRIMARY_COLOR'),
                color=UIConfig.get_color('TEXT_COLOR')
            )
            status_btn.bind(on_press=lambda x, tid=task_id: self.toggle_task_status(tid))
            task_layout.add_widget(status_btn)

            task_info = BoxLayout(orientation='vertical', spacing=2)
            title_label = Label(
                text=title,
                size_hint_y=None,
                height=25,
                color=UIConfig.get_color('TEXT_COLOR'),
                text_size=(self.width - 200, None)
            )
            category_text = f"[{category_name}] {tags}" if category_name else f"[No Category] {tags}"
            category_label = Label(
                text=category_text,
                size_hint_y=None,
                height=20,
                color=UIConfig.get_color('TEXT_COLOR'),
                font_size=12
            )
            task_info.add_widget(title_label)
            task_info.add_widget(category_label)
            task_layout.add_widget(task_info)

            categorize_btn = Button(
                text="Categorize",
                size_hint=(None, None),
                size=(100, 40),
                background_color=UIConfig.get_color('SECONDARY_COLOR'),
                color=UIConfig.get_color('TEXT_COLOR')
            )
            categorize_btn.bind(on_press=lambda x, tid=task_id, ttitle=title: 
                              self.open_categorize_popup(tid, ttitle))
            task_layout.add_widget(categorize_btn)

            self.tasks_container.add_widget(task_layout)

    def show_error(self, message):
        """Show error popup"""
        error_popup = Popup(
            title="Error",
            content=Label(
                text=message,
                color=UIConfig.get_color('TEXT_COLOR')
            ),
            size_hint=(0.6, 0.3),
            background_color=UIConfig.get_color('SURFACE_COLOR')
        )
        error_popup.open()