from kivy.app import App                                        # Class chính để tạo ứng dụng
from kivy.uix.widget import Widget                              # Widget cơ bản
from kivy.uix.boxlayout import BoxLayout                        # Layout sắp xếp widget theo hàng cột
from kivy.uix.label import Label                                # Widget hiển thị text
from kivy.uix.image import Image                                # Widget hiển thị hình ảnh
from kivy.uix.textinput import TextInput                        # Widget nhập text
from kivy.uix.button import Button                              # Widget nút bấm
from kivy.uix.checkbox import CheckBox                          # Widget checkbox
from kivy.uix.screenmanager import ScreenManager, Screen        # Quản lý nhiều màn hình
from kivy.uix.spinner import Spinner                            # Widget dropdown
from kivy.uix.popup import Popup                                # Widget popup dialog
from kivy.uix.scrollview import ScrollView                      # Widget cuộn
from kivy.graphics import Color, Rectangle                      # Vẽ hình và màu sắc
from kivy.uix.progressbar import ProgressBar                    # Thanh tiến trình
from kivy.properties import DictProperty                        # Thuộc tính dict của kivy
from kivy.clock import Clock                                    # Lên lịch các tác vụ
from models.category import CategoryScreen
from models.deadline import DeadlineScreen

from datetime import datetime
from collections import defaultdict
import sqlite3
import json
import os
import traceback                                                # Thư viện in chi tiết lỗi




# =============================================================================
# UI DESIGN CONFIGURATION
# =============================================================================

class UIConfig:
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
    theme_data = LIGHT_THEME

    # Sizes
    BUTTON_HEIGHT = 48              # Chiều cao nút
    INPUT_HEIGHT = 48               # Chiều cao ô input
    TASK_HEIGHT = 60                # Chiều cao mỗi ô Task
    BORDER_RADIUS = 12              # Độ bo góc
    PADDING = 16                    # Khoảng các padding
    SPACING = 12                    # Khoảng cách giữa các widget

    # Typography
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
# DATABASE CLASS
# =============================================================================

class TodoDB:
    def __init__(self):
        try:
            self.conn = sqlite3.connect("data/todo.db")
            self.create_table()
            self.create_deadline_table()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise

    # Tạo bảng Task
    def create_table(self):
        try:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS tasks
                                 (id INTEGER PRIMARY KEY,
                                  title TEXT NOT NULL,
                                  done INTEGER DEFAULT 0,
                                  date TEXT NOT NULL,
                                  category_id INTEGER,
                                  tags TEXT,
                                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")
            traceback.print_exc()
            raise

    # Tạo bảng deadlines
    def create_deadline_table(self):
        try:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS task_deadlines
                                (task_id INTEGER,
                                deadline_date TEXT NOT NULL,
                                deadline_time TEXT,
                                FOREIGN KEY (task_id) REFERENCES tasks(id))''')
            
            for column in ['deadline_date', 'deadline_time', 'priority']:
                try:
                    self.conn.execute(f'ALTER TABLE tasks ADD COLUMN {column} TEXT')
                except sqlite3.OperationalError:
                    pass
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating deadline table: {e}")
            raise

    # Thêm Task mới
    def add_task(self, title):
        try:
            if not title or not title.strip():
                raise ValueError("Task title cannot be empty")
            
            today = datetime.today().strftime('%Y-%m-%d') # Lấy ngày hiện tại
            self.conn.execute("INSERT INTO tasks (title, done, date) VALUES (?, 0, ?)", 
                            (title.strip(), today))
            self.conn.commit()
            return True
        except (sqlite3.Error, ValueError) as e:
            print(f"Error adding task: {e}")
            return False
        
    # Lấy danh sách Tasks theo filter
    def get_tasks(self, filter_status='all'):
        try:
            if filter_status == 'completed':
                cursor = self.conn.execute("SELECT id, title, done FROM tasks WHERE done = 1 ORDER BY id DESC")
            elif filter_status == 'pending':
                cursor = self.conn.execute("SELECT id, title, done FROM tasks WHERE done = 0 ORDER BY id DESC")
            else:
                cursor = self.conn.execute("SELECT id, title, done FROM tasks ORDER BY done ASC, id DESC")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting tasks: {e}")
            return []

    # Đánh dấu Task đã hoàn thành, chưa hoàn thành
    def mark_done(self, task_id, done):
        try:
            self.conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (done, task_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error marking task: {e}")
            return False

    # Xóa Task
    def delete_task(self, task_id):
        try:
            self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting task: {e}")
            return False

    # Thống kê Task hoàn thành theo ngày
    def get_stats(self):
        try:
            cursor = self.conn.execute("SELECT date, COUNT(*) FROM tasks WHERE done = 1 GROUP BY date ORDER BY date") # Truy vấn cơ sở dữ liệu, để phục vụ cho việc thống kê
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


# =============================================================================
# CUSTOM UI COMPONENTS
# =============================================================================

class ModernButton(Button):
    def __init__(self, button_type='primary', **kwargs):
        super().__init__(**kwargs)
        self.button_type = button_type
        self.size_hint_y = None                         # Không tự động điều chỉnh chiều cao
        self.height = UIConfig.BUTTON_HEIGHT
        self.font_size = UIConfig.BODY_FONT_SIZE
        self.bold = True
        self.update_colors()
        self.color = (1, 1, 1, 1)                       # Thêm dòng này để đặt màu chữ trắng


    def update_colors(self):
        color_map = {
            'primary': UIConfig.get_color('PRIMARY_COLOR'),
            'secondary': UIConfig.get_color('SECONDARY_COLOR'),
            'success': UIConfig.get_color('SUCCESS_COLOR'),
            'danger': UIConfig.get_color('DANGER_COLOR')
        }
        # Lấy màu background theo loại button
        self.background_color = color_map.get(self.button_type, UIConfig.get_color('PRIMARY_COLOR'))
        # Lên lịch đặt màu chữ sau 1 frame
        Clock.schedule_once(lambda dt: setattr(self, 'color', (1, 1, 1, 1)), 0)



class ModernTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = UIConfig.INPUT_HEIGHT
        self.font_size = UIConfig.BODY_FONT_SIZE
        self.background_color = UIConfig.get_color('SURFACE_COLOR')
        self.foreground_color = UIConfig.get_color('TEXT_COLOR')
        self.padding = [UIConfig.PADDING//2, UIConfig.PADDING//2]


# =============================================================================
# SCREENS
# =============================================================================


class ConfirmDialog(Popup):
    def __init__(self, message, callback, **kwargs):
        super().__init__(**kwargs)
        self.title = "Confirm"
        self.size_hint = (0.8, 0.4)
        self.callback = callback
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        content.add_widget(Label(
            text=message,
            text_size=(None, None),
            color=(1, 1, 1, 1) # luôn hiện màu trắng bất kể theme nào
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
        self.callback()
        self.dismiss()


    def on_no(self, instance):
        self.dismiss()



class TodoScreen(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db # Lưu reference đến database
        self.orientation = 'vertical'
        self.spacing = UIConfig.SPACING
        self.padding = UIConfig.PADDING
        
        # Background
        with self.canvas.before:
            Color(*UIConfig.get_color('BACKGROUND_COLOR'))
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg) # Thay đổi kích thước
        
        # Input section
        input_section = BoxLayout(orientation='horizontal', size_hint_y=None, height=UIConfig.INPUT_HEIGHT, spacing=UIConfig.SPACING)
        
        self.task_input = ModernTextInput(hint_text="Enter new task!", multiline=False)
        self.task_input.bind(on_text_validate=self.add_task)
        
        add_btn = ModernButton(text="Add", button_type='primary', size_hint_x=None, width=80)
        add_btn.bind(on_press=self.add_task)
        
        input_section.add_widget(self.task_input)
        input_section.add_widget(add_btn)
        self.add_widget(input_section)
        
        # Filter section
        filter_section = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=UIConfig.SPACING)
        filter_section.add_widget(Label(
            text="Filter:",
            size_hint_x=None,
            width=50,
            color=UIConfig.get_color('TEXT_COLOR')
        ))
        
        self.filter_spinner = Spinner(
            text='All',
            values=['All', 'Not Finished', 'Finished'],             # Các tùy chọn
            size_hint_x=None,
            width=150,
            background_color=UIConfig.get_color('SURFACE_COLOR'),
            color=UIConfig.get_color('WHITE_COLOR')
        )   
        self.filter_spinner.bind(text=self.on_filter_change)
        
        filter_section.add_widget(self.filter_spinner)
        
        self.summary_label = Label(
            text="",
            size_hint_x=1,
            halign='right',
            color=UIConfig.get_color('DISABLED_COLOR')
        )
        filter_section.add_widget(self.summary_label)
        
        self.add_widget(filter_section)
        
        # Tasks container with scroll
        scroll = ScrollView()
        self.tasks_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=UIConfig.SPACING//2)
        self.tasks_container.bind(minimum_height=self.tasks_container.setter('height'))
        scroll.add_widget(self.tasks_container)
        self.add_widget(scroll)
        
        self.refresh_tasks()


    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*UIConfig.get_color('BACKGROUND_COLOR'))
            self.bg = Rectangle(pos=self.pos, size=self.size)


    def add_task(self, _):
        title = self.task_input.text.strip()
        if not title:
            popup = Popup(
                title="Notification",
                content=Label(text="Please enter a task title!", color=(1, 1, 1, 1)),
                size_hint=(0.8, 0.3)
            )
            popup.open()
            # self.show_message("Please enter a task title!")
            return
            
        success = self.db.add_task(title)
        if success:
            self.task_input.text = ''
            self.refresh_tasks()
        else:
            popup = Popup(
                title="Error",
                content=Label(text="Error Adding task!", color=(1, 1, 1, 1)),
                size_hint=(0.8, 0.3)
            )
            popup.open()
            # self.show_message("Error adding task!")


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
        summary = self.db.get_task_summary()
        self.summary_label.text = f"Total: {summary['total']} | Completed: {summary['completed']} | Remaining: {summary['pending']}"
        current_filter = self.get_current_filter()
        tasks = self.db.get_tasks(current_filter)
        
        if not tasks:
            self.tasks_container.add_widget(
                Label(
                    text="No tasks available!",
                    size_hint_y=None,
                    height=40,
                    color=UIConfig.get_color('TEXT_COLOR')
                )
            )
            return
        
        for task_id, title, done in tasks:
            self.create_task_widget(task_id, title, bool(done))


    def create_task_widget(self, task_id, title, done):
        box = BoxLayout(size_hint_y=None, height=UIConfig.TASK_HEIGHT, spacing=UIConfig.SPACING, padding=(5, 0))
        # Vẽ background cho Task
        with box.canvas.before:
            Color(*UIConfig.get_color('SURFACE_COLOR'))
            box.bg = Rectangle(pos=box.pos, size=box.size)
        # bind để cập nhật background khi thay đổi kích thước
        box.bind(pos=lambda w, *args: setattr(w.bg, 'pos', w.pos),
                size=lambda w, *args: setattr(w.bg, 'size', w.size))
        
        checkbox = CheckBox(
            active=done,
            size_hint_x=None, # Không tự động điều chỉnh chiều rộng
            width=40,
            color=UIConfig.get_color('SUCCESS_COLOR') if done else UIConfig.get_color('PRIMARY_COLOR')
        )
        checkbox.bind(active=lambda cb, val, task_id=task_id: self.toggle_task(task_id, val))
        
        label_text = f"[s]{title}[/s]" if done else title # Gạch ngang nếu đã hoàn thành
        label = Label(
            text=label_text,
            markup=True,
            text_size=(None, None),
            halign='left', # Căn trái
            color=UIConfig.get_color('TEXT_COLOR')
        )
    
        delete_btn = ModernButton(
            text="Delete",
            button_type='danger',
            size_hint_x=None,
            width=65
        )
        delete_btn.bind(on_press=lambda btn, task_id=task_id, title=title: self.confirm_delete(task_id, title))
        
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
            content=Label(text=message, color=UIConfig.get_color('TEXT_COLOR')),
            size_hint=(0.8, 0.3)
        )
        popup.open()


    def update_theme(self):
        self.update_bg()
        self.refresh_tasks()
        for widget in self.walk():
            if isinstance(widget, Label):
                widget.color = UIConfig.get_color('TEXT_COLOR')
            elif isinstance(widget, ModernButton):
                widget.update_colors()
            elif isinstance(widget, ModernTextInput):
                widget.background_color = UIConfig.get_color('SURFACE_COLOR')
                widget.foreground_color = UIConfig.get_color('TEXT_COLOR')
            elif isinstance(widget, Spinner):
                widget.background_color = UIConfig.get_color('SURFACE_COLOR')
                widget.color = UIConfig.get_color('TEXT_COLOR')


#==============
#Màn hình thống kê
#==============


class StatsScreen(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.orientation = 'vertical'
        self.padding = UIConfig.PADDING
        self.spacing = UIConfig.SPACING
        
        with self.canvas.before:
            Color(*UIConfig.get_color('BACKGROUND_COLOR'))
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)
        # Lấy thống kê tổng quan
        summary = self.db.get_task_summary()
        summary_text = f"""
Overall Statistics:
• Total tasks: {summary['total']}
• Completed: {summary['completed']}
• Not completed: {summary['pending']}
• Completion rate: {(summary['completed']/summary['total']*100 if summary['total'] > 0 else 0):.2f}%
        """.strip()
        
        self.summary_label = Label(
            text=summary_text,
            size_hint_y=None,
            height=100,
            text_size=(None, None),
            halign='left',
            color=UIConfig.get_color('TEXT_COLOR')
        )
        self.add_widget(self.summary_label)
        
        self.create_chart()


    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*UIConfig.get_color('BACKGROUND_COLOR'))
            self.bg = Rectangle(pos=self.pos, size=self.size)


    def create_chart(self):
        stats = self.db.get_stats() # Lấy dữ liệu thống kê từ database
        
        if not stats:
            no_data_label = Label(
                text="No completed tasks data available yet.\nComplete some tasks to see statistics!",
                size_hint_y=None,
                height=100,
                font_size=16,
                color=UIConfig.get_color('TEXT_COLOR')  # Đảm bảo màu chữ theo theme
            )
            self.add_widget(no_data_label)
            return
        
        # Chart title
        title_label = Label(
            text="Tasks Completed by Date",
            size_hint_y=None,
            height=40,
            font_size=18,
            bold=True,
            color=UIConfig.get_color('TEXT_COLOR')  # Đảm bảo màu chữ theo theme
        )
        self.add_widget(title_label)
        
        # Create scrollable container for chart data
        scroll = ScrollView()
        chart_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8)
        chart_container.bind(minimum_height=chart_container.setter('height'))
        
        # Sort by date
        sorted_stats = sorted(stats.items()) # Sắp xếp theo ngày
        max_value = max(stats.values()) if stats else 1 # Tìm số task đã hoàn thành trong 1 ngày lớn nhất 
        
        for date, count in sorted_stats: # lấy date và count từ db
            # Create row for each date
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=15, spacing=10)
            
            # Date label
            date_label = Label(
                text=date, 
                size_hint_x=None, 
                width=100, 
                halign='right',
                font_size=12,
                color=UIConfig.get_color('TEXT_COLOR')  # Cập nhật màu chữ theo theme
            )
            row.add_widget(date_label)
            
            # Progress bar container
            progress_container = BoxLayout(orientation='horizontal', size_hint_x=1) # Sắp xếp các bố cục con theo chiều ngang
            
            # Create visual bar using ProgressBar
            progress_bar = ProgressBar(
                max=max_value,
                value=count,  #count này lấy từ db (lưu trong hàm get_stats())
                size_hint_y=None,
                height=20
            )
            progress_container.add_widget(progress_bar)
            
            row.add_widget(progress_container)
            
            # Count label
            count_label = Label(
                text=f"{count} task{'s' if count != 1 else ''}", 
                size_hint_x=None, 
                width=80, 
                halign='left',
                font_size=12,
                color=UIConfig.get_color('TEXT_COLOR')  # Cập nhật màu chữ theo theme
            )
            row.add_widget(count_label)
            
            chart_container.add_widget(row)
        
        # Add total summary
        total_completed = sum(stats.values())
        total_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        # total_row.add_widget(Label(text="", size_hint_x=None, width=100))
        total_row.add_widget(Label(text="--" * 50, size_hint_x=1, halign='center', color=UIConfig.get_color("TEXT_COLOR")))
        # total_row.add_widget(Label(text="", size_hint_x=None, width=80))
        chart_container.add_widget(total_row)
        
        summary_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=35, spacing=10)
        summary_row.add_widget(Label(
            text="TOTAL", 
            size_hint_x=None, 
            width=100, 
            halign='right', 
            bold=True,
            color=UIConfig.get_color('TEXT_COLOR')  # Cập nhật màu chữ theo theme
        ))
        summary_row.add_widget(Label(text="", size_hint_x=1))
        summary_row.add_widget(Label(
            text=f"{total_completed} task{'s' if total_completed != 1 else ''}", 
            size_hint_x=None, 
            width=80, 
            halign='left', 
            bold=True,
            color=UIConfig.get_color('TEXT_COLOR')  # Cập nhật màu chữ theo theme
        ))
        chart_container.add_widget(summary_row)
        
        scroll.add_widget(chart_container)
        self.add_widget(scroll)


    def update_theme(self):
        self.update_bg()
        self.summary_label.color = UIConfig.get_color('TEXT_COLOR')
        self.clear_widgets()
        self.add_widget(self.summary_label)
        self.create_chart()



# =============================================================================
# MAIN APPLICATION
# =============================================================================


class MainApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_listeners = [] # Danh sách các widget cần cập nhật theme


    def create_icon_button(self, text, icon_source, button_type='primary'):
            """Phương thức helper tạo button có icon (đặt trong class MainApp)"""
            btn = ModernButton(button_type=button_type)
            btn.text = ""  # Xóa text mặc định
            
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
        self.size = (360, 640) # Kích thước cửa sổ
        self.title = "Todo App - Task Management"
        
        UIConfig.load_theme() # Load theme đã lưu
        
        try:
            self.db = TodoDB() # Khởi tạo database
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            return Label(text="Database initialization error!")
        
        self.sm = ScreenManager()
        # Tạo màn hình todo
        self.todo_screen = Screen(name='todo')
        self.todo_widget = TodoScreen(self.db)
        self.todo_screen.add_widget(self.todo_widget)
        self.sm.add_widget(self.todo_screen)
        self.theme_listeners.append(self.todo_widget)
        
        self.stats_screen = Screen(name='stats')
        self.sm.add_widget(self.stats_screen)
        
        self.category_screen = Screen(name='categories')
        self.category_screen.add_widget(CategoryScreen(self.db))
        self.sm.add_widget(self.category_screen)
        self.theme_listeners.append(self.category_screen.children[0])
        
        self.deadline_screen = Screen(name='deadlines')
        self.deadline_screen.add_widget(DeadlineScreen(self.db))
        self.sm.add_widget(self.deadline_screen)
        self.theme_listeners.append(self.deadline_screen.children[0])
        
        root = BoxLayout(orientation='vertical') # Các widget con sẽ được sắp xếp theo chiều dọc (từ trên xuống dưới)
        root.add_widget(self.sm)
        
        nav_buttons = BoxLayout(size_hint_y=None, height=60, spacing=5, padding=5)
        # Vẽ background cho thanh điều hướng
        with nav_buttons.canvas.before:
            Color(*UIConfig.get_color('SURFACE_COLOR'))
            nav_buttons.bg = Rectangle(pos=nav_buttons.pos, size=nav_buttons.size)
        nav_buttons.bind(pos=lambda w, *args: setattr(w.bg, 'pos', w.pos),
                        size=lambda w, *args: setattr(w.bg, 'size', w.size))
        
        '''Các nút điều hướng'''
        # todo_btn = self.create_icon_button("Tasks", "icons/todo_icon.png", 'primary')
        # todo_btn.bind(on_press=lambda _: setattr(self.sm, 'current', 'todo'))

        self.todo_btn = ModernButton(text="📝 Tasks", button_type='primary', color=(1, 1, 1, 1))
        self.todo_btn.bind(on_press=lambda _: setattr(self.sm, 'current', 'todo'))
        
        self.stats_btn = ModernButton(text="📊 Statistics", button_type='secondary', color=(1, 1, 1, 1))
        self.stats_btn.bind(on_press=lambda _: self.switch_to_stats())
        
        self.category_btn = ModernButton(text="🏷️ Category", button_type='success', color=(1, 1, 1, 1))
        self.category_btn.bind(on_press=lambda _: setattr(self.sm, 'current', 'categories'))
        
        self.deadline_btn = ModernButton(text="⏰ Deadline", button_type='warning', color=(1, 1, 1, 1))
        self.deadline_btn.bind(on_press=lambda _: self.switch_to_deadlines())
        
        '''Nút chuyển theme Dark/Light'''
        self.theme_btn = ModernButton(text="D" if UIConfig.current_theme == 'light' else "L", button_type='secondary', size_hint_x=None, width=50)
        self.theme_btn.bind(on_press=self.toggle_theme)
        
        nav_buttons.add_widget(self.todo_btn)
        nav_buttons.add_widget(self.stats_btn)
        nav_buttons.add_widget(self.category_btn)
        nav_buttons.add_widget(self.deadline_btn)
        nav_buttons.add_widget(self.theme_btn)
        
        root.add_widget(nav_buttons)
        return root


    def toggle_theme(self, instance):
        new_theme = 'dark' if UIConfig.current_theme == 'light' else 'light'
        UIConfig.set_theme(new_theme)
        instance.text = "D" if new_theme == 'light' else "L"

        # Update theme cho các screen
        for listener in self.theme_listeners:
            if hasattr(listener, 'update_theme'):  
                listener.update_theme()

        # Đảm bảo rằng màu của chữ trong các nút đều là màu trắng trong bất kể theme nào
        def fix_nav_colors(dt):
            self.todo_btn.color = (1, 1, 1, 1)
            self.stats_btn.color = (1, 1, 1, 1)
            self.category_btn.color = (1, 1, 1, 1)
            self.deadline_btn.color = (1, 1, 1, 1)
            self.theme_btn.color = (1, 1, 1, 1)
        
        Clock.schedule_once(fix_nav_colors, 0.1)


    def switch_to_stats(self):
        if 'stats' in [screen.name for screen in self.sm.screens]:
            self.sm.remove_widget(self.stats_screen)
        
        self.stats_screen = Screen(name='stats')
        self.stats_widget = StatsScreen(self.db)
        self.stats_screen.add_widget(self.stats_widget)
        self.sm.add_widget(self.stats_screen)
        self.theme_listeners.append(self.stats_widget)
        self.sm.current = 'stats'


    def switch_to_categories(self):
        if 'categories' in [screen.name for screen in self.sm.screens]:
            self.sm.remove_widget(self.category_screen)
        
        self.category_screen = Screen(name='categories')
        self.category_screen.add_widget(CategoryScreen(self.db))
        self.sm.add_widget(self.category_screen)
        self.theme_listeners.append(self.category_screen.children[0])
        self.sm.current = 'categories'


    def switch_to_deadlines(self):
        if 'deadlines' in [screen.name for screen in self.sm.screens]:
            self.sm.remove_widget(self.deadline_screen)
        
        self.deadline_screen = Screen(name='deadlines')
        self.deadline_screen.add_widget(DeadlineScreen(self.db))
        self.sm.add_widget(self.deadline_screen)
        self.theme_listeners.append(self.deadline_screen.children[0])
        self.sm.current = 'deadlines'


    def on_stop(self):
        if hasattr(self, 'db'):
            self.db.close()



if __name__ == '__main__':
    MainApp().run()