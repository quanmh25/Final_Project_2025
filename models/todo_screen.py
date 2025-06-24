from kivy.uix.boxlayout import BoxLayout                        # Layout for arranging widgets in rows/columns
from kivy.uix.label import Label                                # Widget for displaying text
from kivy.uix.textinput import TextInput                        # Widget for text input
from kivy.uix.button import Button                              # Button widget
from kivy.uix.checkbox import CheckBox                          # Checkbox widget
from kivy.uix.spinner import Spinner                            # Dropdown widget
from kivy.uix.popup import Popup                                # Popup dialog widget
from kivy.uix.scrollview import ScrollView                      # Scrollable widget
from kivy.graphics import Color, Rectangle                      # Graphics for drawing shapes and colors
from kivy.clock import Clock                                    # Task scheduling

from models.category import CategoryScreen
from models.deadline import DeadlineScreen, DeadlinePopup, DeadlineDB
from models.custom_ui import UIConfig, ModernButton, ModernTextInput, ConfirmDialog
from models.stats_screen import StatsScreen
from models.database import TodoDB

from datetime import datetime
from collections import defaultdict
import sqlite3
import json
import os


class TodoScreen(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db  # Store reference to database
        self.orientation = 'vertical'
        self.spacing = UIConfig.SPACING
        self.padding = UIConfig.PADDING
        
        # Background
        with self.canvas.before:
            Color(*UIConfig.get_color('BACKGROUND_COLOR'))
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)  # Update on size change
        
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
            values=['All', 'Not Finished', 'Finished'],  # Filter options
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
        """Update background when widget size changes"""
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*UIConfig.get_color('BACKGROUND_COLOR'))
            self.bg = Rectangle(pos=self.pos, size=self.size)

    def add_task(self, _):
        """Add a new task to the database"""
        title = self.task_input.text.strip()
        if not title:
            popup = Popup(
                title="Notification",
                content=Label(text="Please enter a task title!", color=(1, 1, 1, 1)),
                size_hint=(0.8, 0.3)
            )
            popup.open()
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

    def on_filter_change(self, spinner, text):
        """Handle filter change event"""
        self.refresh_tasks()

    def get_current_filter(self):
        """Get current filter setting"""
        filter_map = {
            'All': 'all',
            'Not Finished': 'pending',
            'Finished': 'completed'
        }
        return filter_map.get(self.filter_spinner.text, 'all')

    def refresh_tasks(self):
        """Refresh the task list display"""
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
        """Create a widget for displaying a single task"""
        box = BoxLayout(size_hint_y=None, height=UIConfig.TASK_HEIGHT, spacing=UIConfig.SPACING, padding=(5, 0))
        
        # Draw background for task
        with box.canvas.before:
            Color(*UIConfig.get_color('SURFACE_COLOR'))
            box.bg = Rectangle(pos=box.pos, size=box.size)
        # Bind to update background when size changes
        box.bind(pos=lambda w, *args: setattr(w.bg, 'pos', w.pos),
                size=lambda w, *args: setattr(w.bg, 'size', w.size))
        
        checkbox = CheckBox(
            active=done,
            size_hint_x=None,  # Don't auto-adjust width
            width=40,
            color=UIConfig.get_color('SUCCESS_COLOR') if done else UIConfig.get_color('PRIMARY_COLOR')
        )
        checkbox.bind(active=lambda cb, val, task_id=task_id: self.toggle_task(task_id, val))
        
        label_text = f"[s]{title}[/s]" if done else title  # Strike through if completed
        label = Label(
            text=label_text,
            markup=True,
            text_size=(None, None),
            halign='left',  # Left align
            color=UIConfig.get_color('TEXT_COLOR')
        )
        
        deadline_btn = ModernButton(
            text="Add Deadline", 
            size_hint_x=None, 
            width=100,
            button_type='warning'
        )
        deadline_btn.bind(on_press=lambda btn, tid=task_id: self.open_deadline_popup(tid, title))
                          
        delete_btn = ModernButton(
            text="Delete",
            button_type='danger',
            size_hint_x=None,
            width=65
        )
        delete_btn.bind(on_press=lambda btn, task_id=task_id, title=title: self.confirm_delete(task_id, title))
        
        box.add_widget(checkbox)
        box.add_widget(label)
        box.add_widget(deadline_btn)
        box.add_widget(delete_btn)
        
        self.tasks_container.add_widget(box)

    def toggle_task(self, task_id, done):
        """Toggle task completion status"""
        success = self.db.mark_done(task_id, int(done))
        if success:
            self.refresh_tasks()
        else:
            self.show_message("Error updating task!")

    def confirm_delete(self, task_id, title):
        """Show confirmation dialog before deleting task"""
        dialog = ConfirmDialog(
            f"Are you sure you want to delete this task:\n'{title}'?",
            lambda: self.delete_task(task_id)
        )
        dialog.open()

    def open_deadline_popup(self, task_id, task_title):
        """Open deadline setting popup"""
        deadline_db = DeadlineDB()
        popup = DeadlinePopup(
            task_id, 
            task_title, 
            deadline_db=deadline_db,  
            callback=self.refresh_tasks
        )
        popup.open()

    def delete_task(self, task_id):
        """Delete a task from the database"""
        success = self.db.delete_task(task_id)
        if success:
            self.refresh_tasks()
        else:
            self.show_message("Error deleting task!")

    def show_message(self, message):
        """Show a popup message"""
        popup = Popup(
            title="Notification",
            content=Label(text=message, color=UIConfig.get_color('TEXT_COLOR')),
            size_hint=(0.8, 0.3)
        )
        popup.open()

    def update_theme(self):
        """Update UI theme colors"""
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