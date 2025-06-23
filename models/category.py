import sqlite3
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout


class CategoryDB:
    def __init__(self, db_path="data/todo.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_category_tables()
    
    def create_category_tables(self):
        try:
            # Create categories table
            self.conn.execute('''CREATE TABLE IF NOT EXISTS categories
                                 (id INTEGER PRIMARY KEY,
                                  name TEXT UNIQUE NOT NULL,
                                  icon TEXT DEFAULT '📋',
                                  color TEXT DEFAULT '#4CAF50',
                                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            # Add category column to tasks table if not exists
            try:
                self.conn.execute('ALTER TABLE tasks ADD COLUMN category_id INTEGER')
                self.conn.execute('ALTER TABLE tasks ADD COLUMN tags TEXT')
            except sqlite3.OperationalError:
                pass  # Columns already exist
            
            # Create default categories
            default_categories = [
                ('Work', '💼', '#2196F3'),
                ('Personal', '👤', '#4CAF50'), 
                ('Study', '🎓', '#FF9800'),
                ('Health', '🏥', '#F44336'),
                ('Shopping', '🛒', '#9C27B0'),
                ('Home', '🏠', '#795548')
            ]
            
            for name, icon, color in default_categories:
                try:
                    self.conn.execute('INSERT INTO categories (name, icon, color) VALUES (?, ?, ?)',
                                    (name, icon, color))
                except sqlite3.IntegrityError:
                    pass  # Category already exists
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating category tables: {e}")
    
    def add_category(self, name, icon='📋', color='#4CAF50'):
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
            # First, remove category from tasks
            self.conn.execute('UPDATE tasks SET category_id = NULL WHERE category_id = ?', 
                            (category_id,))
            # Then delete the category
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
            cursor = self.conn.execute('''SELECT c.name, c.icon, 
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
            # Tags stored as comma-separated string
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
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Name input
        content.add_widget(Label(text="Category Name:", size_hint_y=None, height=30))
        self.name_input = TextInput(size_hint_y=None, height=40, multiline=False)
        content.add_widget(self.name_input)
        
        # Icon input
        content.add_widget(Label(text="Icon (emoji):", size_hint_y=None, height=30))
        self.icon_input = TextInput(text="📋", size_hint_y=None, height=40, multiline=False)
        content.add_widget(self.icon_input)
        
        # Color input
        content.add_widget(Label(text="Color (hex code):", size_hint_y=None, height=30))
        self.color_input = TextInput(text="#4CAF50", size_hint_y=None, height=40, multiline=False)
        content.add_widget(self.color_input)
        
        # Buttons
        buttons = BoxLayout(spacing=10, size_hint_y=None, height=50)
        
        save_btn = Button(text="Save")
        save_btn.bind(on_press=self.save_category)
        
        cancel_btn = Button(text="Cancel")
        cancel_btn.bind(on_press=self.dismiss)
        
        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        
        self.content = content
    
    def save_category(self, instance):
        name = self.name_input.text.strip()
        icon = self.icon_input.text.strip() or "📋"
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
            content=Label(text=message),
            size_hint=(0.6, 0.3)
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
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Category selection
        content.add_widget(Label(text="Select Category:", size_hint_y=None, height=30))
        
        categories = self.category_db.get_categories()
        category_options = ["None"] + [f"{icon} {name}" for _, name, icon, _ in categories]
        
        self.category_spinner = Spinner(
            text="None",
            values=category_options,
            size_hint_y=None,
            height=40
        )
        content.add_widget(self.category_spinner)
        
        # Tags input
        content.add_widget(Label(text="Tags (comma-separated):", size_hint_y=None, height=30))
        self.tags_input = TextInput(size_hint_y=None, height=40, multiline=False,
                                  hint_text="work, urgent, meeting")
        content.add_widget(self.tags_input)
        
        # Buttons
        buttons = BoxLayout(spacing=10, size_hint_y=None, height=50)
        
        save_btn = Button(text="Save")
        save_btn.bind(on_press=self.save_categorization)
        
        cancel_btn = Button(text="Cancel")
        cancel_btn.bind(on_press=self.dismiss)
        
        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        
        self.content = content
        self.categories = categories
    
    def save_categorization(self, instance):
        selected_text = self.category_spinner.text
        category_id = None
        
        if selected_text != "None":
            # Find category ID from selection
            for cat_id, name, icon, _ in self.categories:
                if selected_text == f"{icon} {name}":
                    category_id = cat_id
                    break
        
        # Set category
        self.category_db.set_task_category(self.task_id, category_id)
        
        # Set tags
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

        
        # Title and controls
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        title = Label(text="🏷️ Categories & Tags", font_size='18sp')
        header.add_widget(title)
        
        add_category_btn = Button(text="➕ Add Category", size_hint_x=None, width=120)
        add_category_btn.bind(on_press=lambda x: self.add_category())
        header.add_widget(add_category_btn)
        
        self.add_widget(header)
        
        # Filter section
        filter_section = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        filter_section.add_widget(Label(text="Filter by:", size_hint_x=None, width=80))
        
        self.filter_spinner = Spinner(
            text='All Categories',
            values=['All Categories'],
            size_hint_x=None,
            width=200
        )
        self.filter_spinner.bind(text=self.on_filter_change)
        filter_section.add_widget(self.filter_spinner)
        
        # Tag search
        filter_section.add_widget(Label(text="Tag:", size_hint_x=None, width=40))
        self.tag_search = TextInput(hint_text="Search by tag...", 
                                  size_hint_x=None, width=150, multiline=False)
        self.tag_search.bind(on_text_validate=self.search_by_tag)
        filter_section.add_widget(self.tag_search)
        
        search_btn = Button(text="🔍", size_hint_x=None, width=40)
        search_btn.bind(on_press=lambda x: self.search_by_tag())
        filter_section.add_widget(search_btn)
        
        self.add_widget(filter_section)
        
        # Stats section
        self.stats_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.stats_container.bind(minimum_height=self.stats_container.setter('height'))
        self.add_widget(self.stats_container)
        
        # Tasks container
        scroll = ScrollView()
        self.tasks_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.tasks_container.bind(minimum_height=self.tasks_container.setter('height'))
        scroll.add_widget(self.tasks_container)
        self.add_widget(scroll)
       
        self.refresh_view()
        # Thêm nút back vào header
        back_btn = Button(text="⬅ Back", size_hint_x=None, width=80)
        back_btn.bind(on_press=self.go_back)
        header.add_widget(back_btn)  # Thêm vào header hiện có

    def go_back(self, instance):
        if hasattr(self, 'manager'):
            self.manager.current = 'tasks'  # Quay lại màn hình chính

    def refresh_view(self):
        self.update_filter_options()
        self.update_stats()
        self.refresh_tasks()
    
    def update_filter_options(self):
        categories = self.category_db.get_categories()
        options = ['All Categories'] + [f"{icon} {name}" for _, name, icon, _ in categories]
        self.filter_spinner.values = options
    
    def update_stats(self):
        self.stats_container.clear_widgets()
        
        stats = self.category_db.get_category_stats()
        if stats:
            stats_header = Label(text="📊 Category Statistics", 
                               size_hint_y=None, height=30, font_size='16sp')
            self.stats_container.add_widget(stats_header)
            
            grid = GridLayout(cols=4, size_hint_y=None, spacing=5, padding=5)
            grid.bind(minimum_height=grid.setter('height'))
            
            # Headers
            headers = ["Category", "Total", "Done", "Progress"]
            for header in headers:
                grid.add_widget(Label(text=header, bold=True, size_hint_y=None, height=30))
            
            for name, icon, total, completed in stats:
                if total > 0:
                    progress = f"{completed}/{total} ({completed/total*100:.0f}%)"
                    
                    grid.add_widget(Label(text=f"{icon} {name}", size_hint_y=None, height=30))
                    grid.add_widget(Label(text=str(total), size_hint_y=None, height=30))
                    grid.add_widget(Label(text=str(completed), size_hint_y=None, height=30))
                    grid.add_widget(Label(text=progress, size_hint_y=None, height=30))
            
            self.stats_container.add_widget(grid)
    
    def on_filter_change(self, spinner, text):
        self.refresh_tasks()
    
    def refresh_tasks(self):
        self.tasks_container.clear_widgets()
        
        # Get selected category
        selected_category = None
        if self.filter_spinner.text != 'All Categories':
            categories = self.category_db.get_categories()
            for cat_id, name, icon, _ in categories:
                if self.filter_spinner.text == f"{icon} {name}":
                    selected_category = cat_id
                    break
        
        tasks = self.category_db.get_tasks_by_category(selected_category)
        
        if not tasks:
            self.tasks_container.add_widget(
                Label(text="No tasks in this category!", size_hint_y=None, height=40)
            )
            return
        
        current_category = None
        for task_id, title, done, category_name, category_icon in tasks:
            # Add category header if different from previous
            if category_name != current_category:
                current_category = category_name
                header_text = f"{category_icon} {category_name}" if category_name else "📋 Uncategorized"
                header = Label(text=header_text, size_hint_y=None, height=35,
                             font_size='14sp', bold=True)
                self.tasks_container.add_widget(header)
            
            self.create_task_widget(task_id, title, done, category_name, category_icon)
    
    def create_task_widget(self, task_id, title, done, category_name, category_icon):
        box = BoxLayout(size_hint_y=None, height=50, spacing=10, padding=(20, 5))
        
        # Task status
        status = "✅" if done else "⏳"
        
        # Task title with strikethrough if completed
        label_text = f"{status} {title}"
        if done:
            label_text = f"[s]{label_text}[/s]"
        
        task_label = Label(text=label_text, markup=True, text_size=(None, None), halign='left')
        
        # Categorize button
        categorize_btn = Button(text="🏷️", size_hint_x=None, width=40)
        categorize_btn.bind(on_press=lambda x, tid=task_id, ttitle=title: 
                          self.categorize_task(tid, ttitle))
        
        box.add_widget(task_label)
        box.add_widget(categorize_btn)
        
        self.tasks_container.add_widget(box)
    
    def add_category(self):
        popup = CategoryPopup(self.category_db, callback=self.refresh_view)
        popup.open()
    
    def categorize_task(self, task_id, task_title):
        popup = TaskCategoryPopup(task_id, task_title, self.category_db, 
                                callback=self.refresh_view)
        popup.open()
    
    def search_by_tag(self, instance=None):
        tag = self.tag_search.text.strip()
        if not tag:
            self.refresh_tasks()
            return
        
        self.tasks_container.clear_widgets()
        
        tasks = self.category_db.search_tasks_by_tag(tag)
        
        if not tasks:
            self.tasks_container.add_widget(
                Label(text=f"No tasks found with tag '{tag}'!", size_hint_y=None, height=40)
            )
            return
        
        header = Label(text=f"🔍 Search results for '{tag}'", 
                      size_hint_y=None, height=35, font_size='14sp', bold=True)
        self.tasks_container.add_widget(header)

        for task in tasks:
            task_id, title, done, category_name, category_icon, tags = task
            self.create_search_result_widget(
                task_id, title, done, 
                category_name, category_icon, 
                tags, tag  # Thêm tham số tag để highlight
            )        
    
    def create_search_result_widget(self, task_id, title, done, category_name, 
                                   category_icon, tags, search_tag):
        box = BoxLayout(size_hint_y=None, height=60, spacing=10, padding=(20, 5))
        
        # Task status
        status = "✅" if done else "⏳"
        
        # Category info
        category_info = f"{category_icon} {category_name}" if category_name else "📋 Uncategorized"
        
        # Highlight matching tag
        highlighted_tags = tags.replace(search_tag, f"[b]{search_tag}[/b]") if tags else ""
        
        # Task info
        task_text = f"{status} {title}\n{category_info} | Tags: {highlighted_tags}"
        if done:
            task_text = f"[s]{status} {title}[/s]\n{category_info} | Tags: {highlighted_tags}"
        
        task_label = Label(text=task_text, markup=True, text_size=(None, None), 
                          halign='left', valign='middle')
        
        # Categorize button
        categorize_btn = Button(text="🏷️", size_hint_x=None, width=40)
        categorize_btn.bind(on_press=lambda x, tid=task_id, ttitle=title: 
                          self.categorize_task(tid, ttitle))
        
        box.add_widget(task_label)
        box.add_widget(categorize_btn)
        
        self.tasks_container.add_widget(box)