import sqlite3
from datetime import datetime
from collections import defaultdict

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt


class TodoDB:
    def __init__(self):
        try:
            self.conn = sqlite3.connect("data/todo.db")
            self.create_table()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise

    def create_table(self):
        try:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS tasks
                                 (id INTEGER PRIMARY KEY,
                                  title TEXT NOT NULL,
                                  done INTEGER DEFAULT 0,
                                  date TEXT NOT NULL,
                                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")
            raise

    def add_task(self, title):
        try:
            if not title or not title.strip():
                raise ValueError("Task title cannot be empty")
            
            today = datetime.today().strftime('%Y-%m-%d')
            self.conn.execute("INSERT INTO tasks (title, done, date) VALUES (?, 0, ?)", 
                            (title.strip(), today))
            self.conn.commit()
            return True
        except (sqlite3.Error, ValueError) as e:
            print(f"Error adding task: {e}")
            return False

    def get_tasks(self, filter_status='all'):
        try:
            if filter_status == 'completed':
                cursor = self.conn.execute("SELECT id, title, done FROM tasks WHERE done = 1 ORDER BY id DESC")
            elif filter_status == 'pending':
                cursor = self.conn.execute("SELECT id, title, done FROM tasks WHERE done = 0 ORDER BY id DESC")
            else:  # all
                cursor = self.conn.execute("SELECT id, title, done FROM tasks ORDER BY done ASC, id DESC")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting tasks: {e}")
            return []

    def mark_done(self, task_id, done):
        try:
            self.conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (done, task_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error marking task: {e}")
            return False

    def delete_task(self, task_id):
        try:
            self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting task: {e}")
            return False

    def get_stats(self):
        try:
            cursor = self.conn.execute("SELECT date, COUNT(*) FROM tasks WHERE done = 1 GROUP BY date ORDER BY date")
            return dict(cursor.fetchall())
        except sqlite3.Error as e:
            print(f"Error getting stats: {e}")
            return {}

    def get_task_summary(self):
        try:
            cursor = self.conn.execute("SELECT COUNT(*) as total, SUM(done) as completed FROM tasks")
            result = cursor.fetchone()
            total = result[0] if result[0] else 0
            completed = result[1] if result[1] else 0
            pending = total - completed
            return {'total': total, 'completed': completed, 'pending': pending}
        except sqlite3.Error as e:
            print(f"Error getting summary: {e}")
            return {'total': 0, 'completed': 0, 'pending': 0}

    def close(self):
        if self.conn:
            self.conn.close()


class ConfirmDialog(Popup):
    def __init__(self, message, callback, **kwargs):
        super().__init__(**kwargs)
        self.title = "Confirm"
        self.size_hint = (0.8, 0.4)
        self.callback = callback
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=message, text_size=(None, None)))
        
        buttons = BoxLayout(spacing=10, size_hint_y=None, height=40)
        
        yes_btn = Button(text="Yes")
        yes_btn.bind(on_press=self.on_yes)
        
        no_btn = Button(text="No")
        no_btn.bind(on_press=self.on_no)
        
        buttons.add_widget(yes_btn)
        buttons.add_widget(no_btn)
        
        content.add_widget(buttons)
        self.content = content

    def on_yes(self, instance):
        self.callback()
        self.dismiss()

    def on_no(self, instance):
        self.dismiss()


class TodoScreen(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = 10
        
        # Input section
        input_section = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        self.task_input = TextInput(hint_text="Enter new task...", multiline=False)
        self.task_input.bind(on_text_validate=self.add_task)
        
        add_btn = Button(text="Add", size_hint_x=None, width=80)
        add_btn.bind(on_press=self.add_task)
        
        input_section.add_widget(self.task_input)
        input_section.add_widget(add_btn)
        self.add_widget(input_section)
        
        # Filter section
        filter_section = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        filter_section.add_widget(Label(text="Filter:", size_hint_x=None, width=50))
        
        self.filter_spinner = Spinner(
            text='All',
            values=['All', 'Not Finished', 'Finished'],
            size_hint_x=None,
            width=150
        )
        self.filter_spinner.bind(text=self.on_filter_change)
        
        filter_section.add_widget(self.filter_spinner)
        
        # Summary label
        self.summary_label = Label(text="", size_hint_x=1, halign='right')
        filter_section.add_widget(self.summary_label)
        
        self.add_widget(filter_section)
        
        # Tasks container with scroll
        scroll = ScrollView()
        self.tasks_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.tasks_container.bind(minimum_height=self.tasks_container.setter('height'))
        scroll.add_widget(self.tasks_container)
        self.add_widget(scroll)
        
        self.refresh_tasks()

    def add_task(self, _):
        title = self.task_input.text.strip()
        if not title:
            self.show_message("Please enter a task title!")
            return
            
        success = self.db.add_task(title)
        if success:
            self.task_input.text = ''
            self.refresh_tasks()
        else:
            self.show_message("Error adding task!")

    def on_filter_change(self, spinner, text):
        self.refresh_tasks()

    def get_current_filter(self):
        filter_map = {
            'All': 'all',
            'Not Finished': 'pending',
            'Finished': 'completed'
        }
        return filter_map.get(self.filter_spinner.text, 'all')

    def refresh_tasks(self):
        self.tasks_container.clear_widgets()
        
        # Update summary
        summary = self.db.get_task_summary()
        self.summary_label.text = f"Total: {summary['total']} | Completed: {summary['completed']} | Remaining: {summary['pending']}"
        
        # Get filtered tasks
        current_filter = self.get_current_filter()
        tasks = self.db.get_tasks(current_filter)
        
        if not tasks:
            self.tasks_container.add_widget(
                Label(text="No tasks available!", size_hint_y=None, height=40)
            )
            return
        
        for task_id, title, done in tasks:
            self.create_task_widget(task_id, title, bool(done))

    def create_task_widget(self, task_id, title, done):
        box = BoxLayout(size_hint_y=None, height=50, spacing=10, padding=(5, 0))
        
        # Checkbox
        checkbox = CheckBox(active=done, size_hint_x=None, width=40)
        checkbox.bind(active=lambda cb, val, task_id=task_id: self.toggle_task(task_id, val))
        
        # Task title with strikethrough if completed
        label_text = f"[s]{title}[/s]" if done else title
        label = Label(text=label_text, markup=True, text_size=(None, None), halign='left')
        
        # Delete button
        delete_btn = Button(text="Delete", size_hint_x=None, width=60, 
                          background_color=(1, 0.3, 0.3, 1))  # Red color
        delete_btn.bind(on_press=lambda btn, task_id=task_id, title=title: 
                       self.confirm_delete(task_id, title))
        
        box.add_widget(checkbox)
        box.add_widget(label)
        box.add_widget(delete_btn)
        
        self.tasks_container.add_widget(box)

    def toggle_task(self, task_id, done):
        success = self.db.mark_done(task_id, int(done))
        if success:
            self.refresh_tasks()
        else:
            self.show_message("Error updating task!")

    def confirm_delete(self, task_id, title):
        dialog = ConfirmDialog(
            f"Are you sure you want to delete this task:\n'{title}'?",
            lambda: self.delete_task(task_id)
        )
        dialog.open()

    def delete_task(self, task_id):
        success = self.db.delete_task(task_id)
        if success:
            self.refresh_tasks()
        else:
            self.show_message("Error deleting task!")

    def show_message(self, message):
        popup = Popup(
            title="Notification",
            content=Label(text=message),
            size_hint=(0.8, 0.3)
        )
        popup.open()


class StatsScreen(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        
        # Summary section
        summary = self.db.get_task_summary()
        summary_text = f"""
Overall Statistics:
• Total tasks: {summary['total']}
• Completed: {summary['completed']}
• Not completed: {summary['pending']}
• Completion rate: {(summary['completed']/summary['total']*100 if summary['total'] > 0 else 0):.1f}%
        """.strip()
        
        summary_label = Label(text=summary_text, size_hint_y=None, height=100, 
                            text_size=(None, None), halign='left')
        self.add_widget(summary_label)
        
        # Chart section
        self.create_chart()

    def create_chart(self):
        stats = self.db.get_stats()
        
        if not stats:
            self.add_widget(Label(text="No statistics data for completed tasks yet"))
            return
        
        try:
            dates = list(stats.keys())
            values = list(stats.values())
            
            # Sort by date
            sorted_data = sorted(zip(dates, values))
            dates = [item[0] for item in sorted_data]
            values = [item[1] for item in sorted_data]
            
            # Create figure with better styling
            plt.style.use('default')
            fig, ax = plt.subplots(figsize=(10, 6))
            
            bars = ax.bar(dates, values, color='skyblue', edgecolor='navy', alpha=0.7)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                       f'{int(value)}', ha='center', va='bottom')
            
            ax.set_title("Tasks completed by date", fontsize=14, fontweight='bold')
            ax.set_ylabel("Number of tasks", fontsize=12)
            ax.set_xlabel("Date", fontsize=12)
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            self.add_widget(FigureCanvasKivyAgg(fig))
            
        except Exception as e:
            print(f"Error creating chart: {e}")
            self.add_widget(Label(text="Error creating chart"))


class MainApp(App):
    def build(self):
        self.title = "Todo App - Task Management"
        
        try:
            self.db = TodoDB()
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            return Label(text="Database initialization error!")
        
        self.sm = ScreenManager()
        
        # Todo screen
        self.todo_screen = Screen(name='todo')
        self.todo_widget = TodoScreen(self.db)
        self.todo_screen.add_widget(self.todo_widget)
        self.sm.add_widget(self.todo_screen)
        
        # Stats screen
        self.stats_screen = Screen(name='stats')
        self.sm.add_widget(self.stats_screen)
        
        # Main layout
        root = BoxLayout(orientation='vertical')
        root.add_widget(self.sm)
        
        # Navigation buttons
        nav_buttons = BoxLayout(size_hint_y=None, height=60, spacing=5, padding=5)
        
        todo_btn = Button(text="📝 Task Management", 
                         background_color=(0.2, 0.6, 0.8, 1))
        todo_btn.bind(on_press=lambda _: setattr(self.sm, 'current', 'todo'))
        
        stats_btn = Button(text="📊 Statistics", 
                          background_color=(0.8, 0.6, 0.2, 1))
        stats_btn.bind(on_press=lambda _: self.switch_to_stats())
        
        nav_buttons.add_widget(todo_btn)
        nav_buttons.add_widget(stats_btn)
        root.add_widget(nav_buttons)
        
        return root

    def switch_to_stats(self):
        # Refresh stats screen every time we switch to it
        if 'stats' in [screen.name for screen in self.sm.screens]:
            self.sm.remove_widget(self.stats_screen)
        
        self.stats_screen = Screen(name='stats')
        self.stats_screen.add_widget(StatsScreen(self.db))
        self.sm.add_widget(self.stats_screen)
        self.sm.current = 'stats'

    def on_stop(self):
        # Clean up database connection when app closes
        if hasattr(self, 'db'):
            self.db.close()


if __name__ == '__main__':
    MainApp().run()