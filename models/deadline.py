import sqlite3
from datetime import datetime, timedelta
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock


class DeadlineDB:
    def __init__(self, db_path="data/todo.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_deadline_table()
    
    def create_deadline_table(self):
        try:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS task_deadlines
                                 (id INTEGER PRIMARY KEY,
                                  task_id INTEGER,
                                  deadline_date TEXT NOT NULL,
                                  deadline_time TEXT,
                                  reminder_sent INTEGER DEFAULT 0,
                                  FOREIGN KEY (task_id) REFERENCES tasks (id))''')
            
            # Add deadline columns to existing tasks table if not exists
            try:
                self.conn.execute('ALTER TABLE tasks ADD COLUMN deadline_date TEXT')
                self.conn.execute('ALTER TABLE tasks ADD COLUMN deadline_time TEXT')
                self.conn.execute('ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 1')
            except sqlite3.OperationalError:
                pass  # Columns already exist
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating deadline table: {e}")
    
    def set_task_deadline(self, task_id, deadline_date, deadline_time=None):
        try:
            self.conn.execute('''UPDATE tasks 
                               SET deadline_date = ?, deadline_time = ? 
                               WHERE id = ?''', 
                            (deadline_date, deadline_time, task_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error setting deadline: {e}")
            return False
    
    def get_tasks_with_deadlines(self):
        try:
            cursor = self.conn.execute('''SELECT id, title, done, deadline_date, deadline_time, priority
                                        FROM tasks 
                                        WHERE deadline_date IS NOT NULL
                                        ORDER BY deadline_date ASC, deadline_time ASC''')
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting tasks with deadlines: {e}")
            return []
    
    def get_overdue_tasks(self):
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            current_time = datetime.now().strftime('%H:%M')
            
            cursor = self.conn.execute('''SELECT id, title, deadline_date, deadline_time
                                        FROM tasks 
                                        WHERE done = 0 AND deadline_date IS NOT NULL
                                        AND (deadline_date < ? OR 
                                             (deadline_date = ? AND deadline_time < ?))''',
                                     (today, today, current_time))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting overdue tasks: {e}")
            return []
    
    def get_upcoming_tasks(self, days_ahead=3):
        try:
            today = datetime.now()
            future_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            today_str = today.strftime('%Y-%m-%d')
            
            cursor = self.conn.execute('''SELECT id, title, deadline_date, deadline_time
                                        FROM tasks 
                                        WHERE done = 0 AND deadline_date IS NOT NULL
                                        AND deadline_date BETWEEN ? AND ?''',
                                     (today_str, future_date))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting upcoming tasks: {e}")
            return []


class DeadlinePopup(Popup):
    def __init__(self, task_id, task_title, deadline_db, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.task_id = task_id
        self.deadline_db = deadline_db
        self.callback = callback
        
        self.title = f"Set Deadline: {task_title}"
        self.size_hint = (0.8, 0.6)
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Date input
        content.add_widget(Label(text="Deadline Date (YYYY-MM-DD):", 
                               size_hint_y=None, height=30))
        self.date_input = TextInput(
            text=datetime.now().strftime('%Y-%m-%d'),
            size_hint_y=None, height=40, multiline=False
        )
        content.add_widget(self.date_input)
        
        # Time input
        content.add_widget(Label(text="Deadline Time (HH:MM) - Optional:", 
                               size_hint_y=None, height=30))
        self.time_input = TextInput(
            hint_text="23:59",
            size_hint_y=None, height=40, multiline=False
        )
        content.add_widget(self.time_input)
        
        # Buttons
        buttons = BoxLayout(spacing=10, size_hint_y=None, height=50)
        
        save_btn = Button(text="Save Deadline")
        save_btn.bind(on_press=self.save_deadline)
        
        cancel_btn = Button(text="Cancel")
        cancel_btn.bind(on_press=self.dismiss)
        
        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        
        self.content = content
    
    def save_deadline(self, instance):
        date_text = self.date_input.text.strip()
        time_text = self.time_input.text.strip() or None
        
        # Validate date format
        try:
            datetime.strptime(date_text, '%Y-%m-%d')
            if time_text:
                datetime.strptime(time_text, '%H:%M')
        except ValueError:
            self.show_error("Invalid date/time format!")
            return
        
        success = self.deadline_db.set_task_deadline(self.task_id, date_text, time_text)
        if success:
            if self.callback:
                self.callback()
            self.dismiss()
        else:
            self.show_error("Error setting deadline!")
    
    def show_error(self, message):
        error_popup = Popup(
            title="Error",
            content=Label(text=message),
            size_hint=(0.6, 0.3)
        )
        error_popup.open()


class DeadlineScreen(BoxLayout):
    def __init__(self, main_db, **kwargs):
        super().__init__(**kwargs)
        self.main_db = main_db
        self.deadline_db = DeadlineDB()
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = 10
        
        # Title
        title = Label(text="📅 Deadline Management", 
                     size_hint_y=None, height=50,
                     font_size='18sp')
        self.add_widget(title)
        
        # Refresh button
        refresh_btn = Button(text="🔄 Refresh", 
                           size_hint_y=None, height=40)
        refresh_btn.bind(on_press=lambda x: self.refresh_deadlines())
        self.add_widget(refresh_btn)
        
        # Scroll view for tasks
        scroll = ScrollView()
        self.tasks_container = BoxLayout(orientation='vertical', 
                                       size_hint_y=None, spacing=5)
        self.tasks_container.bind(minimum_height=self.tasks_container.setter('height'))
        scroll.add_widget(self.tasks_container)
        self.add_widget(scroll)
        
        # Start reminder checker
        Clock.schedule_interval(self.check_reminders, 300)  # Check every 5 minutes
        
        self.refresh_deadlines()
    
    def refresh_deadlines(self):
        self.tasks_container.clear_widgets()
        
        # Show overdue tasks
        overdue = self.deadline_db.get_overdue_tasks()
        if overdue:
            self.add_section_header("⚠️ OVERDUE TASKS", (1, 0.3, 0.3, 1))
            for task_id, title, deadline_date, deadline_time in overdue:
                self.create_deadline_widget(task_id, title, deadline_date, deadline_time, True)
        
        # Show upcoming tasks
        upcoming = self.deadline_db.get_upcoming_tasks()
        if upcoming:
            self.add_section_header("⏰ UPCOMING DEADLINES", (1, 0.8, 0.2, 1))
            for task_id, title, deadline_date, deadline_time in upcoming:
                if (task_id, title, deadline_date, deadline_time) not in overdue:
                    self.create_deadline_widget(task_id, title, deadline_date, deadline_time, False)
        
        # Show all tasks with deadlines
        all_tasks = self.deadline_db.get_tasks_with_deadlines()
        if all_tasks:
            self.add_section_header("📋 ALL TASKS WITH DEADLINES", (0.2, 0.6, 0.8, 1))
            for task_id, title, done, deadline_date, deadline_time, priority in all_tasks:
                if done:  # Only show completed tasks in this section
                    self.create_completed_deadline_widget(task_id, title, deadline_date, deadline_time)
    
    def add_section_header(self, text, color):
        header = Label(text=text, size_hint_y=None, height=40,
                      color=color, font_size='16sp', bold=True)
        self.tasks_container.add_widget(header)
    
    def create_deadline_widget(self, task_id, title, deadline_date, deadline_time, is_overdue):
        box = BoxLayout(size_hint_y=None, height=60, spacing=10, padding=5)
        
        # Color coding
        bg_color = (1, 0.9, 0.9, 1) if is_overdue else (0.9, 1, 0.9, 1)
        
        # Task info
        deadline_str = deadline_date
        if deadline_time:
            deadline_str += f" {deadline_time}"
        
        task_text = f"{title}\nDeadline: {deadline_str}"
        
        task_label = Label(text=task_text, text_size=(None, None), 
                          halign='left', valign='middle')
        
        # Edit deadline button
        edit_btn = Button(text="Edit", size_hint_x=None, width=60)
        edit_btn.bind(on_press=lambda x, tid=task_id, ttitle=title: 
                     self.edit_deadline(tid, ttitle))
        
        box.add_widget(task_label)
        box.add_widget(edit_btn)
        
        self.tasks_container.add_widget(box)
    
    def create_completed_deadline_widget(self, task_id, title, deadline_date, deadline_time):
        box = BoxLayout(size_hint_y=None, height=50, spacing=10, padding=5)
        
        deadline_str = deadline_date
        if deadline_time:
            deadline_str += f" {deadline_time}"
        
        task_text = f"✅ {title} (Deadline was: {deadline_str})"
        
        task_label = Label(text=task_text, text_size=(None, None), 
                          halign='left', color=(0.6, 0.6, 0.6, 1))
        
        box.add_widget(task_label)
        self.tasks_container.add_widget(box)
    
    def edit_deadline(self, task_id, task_title):
        popup = DeadlinePopup(task_id, task_title, self.deadline_db, 
                            callback=self.refresh_deadlines)
        popup.open()
    
    def check_reminders(self, dt):
        """Check for upcoming deadlines and show reminders"""
        upcoming = self.deadline_db.get_upcoming_tasks(days_ahead=1)
        
        for task_id, title, deadline_date, deadline_time in upcoming:
            # Check if it's within 1 hour
            try:
                deadline_dt = datetime.strptime(deadline_date, '%Y-%m-%d')
                if deadline_time:
                    time_obj = datetime.strptime(deadline_time, '%H:%M').time()
                    deadline_dt = deadline_dt.replace(hour=time_obj.hour, 
                                                    minute=time_obj.minute)
                
                now = datetime.now()
                time_diff = deadline_dt - now
                
                if timedelta(minutes=0) <= time_diff <= timedelta(hours=1):
                    self.show_reminder(title, deadline_date, deadline_time)
                    
            except ValueError:
                continue
    
    def show_reminder(self, title, deadline_date, deadline_time):
        deadline_str = deadline_date
        if deadline_time:
            deadline_str += f" {deadline_time}"
            
        reminder_popup = Popup(
            title="⏰ Deadline Reminder",
            content=Label(text=f"Task: {title}\nDeadline: {deadline_str}"),
            size_hint=(0.8, 0.4)
        )
        reminder_popup.open()
        Clock.schedule_once(lambda dt: reminder_popup.dismiss(), 5)  # Auto-close after 5 seconds