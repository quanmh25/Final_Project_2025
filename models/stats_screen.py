from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.uix.progressbar import ProgressBar

from models.custom_ui import UIConfig


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
        
        # Get overall statistics
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
        # Get statistics data from database
        stats = self.db.get_stats()
        
        if not stats:
            no_data_label = Label(
                text="No completed tasks data available yet.\nComplete some tasks to see statistics!",
                size_hint_y=None,
                height=100,
                font_size=16,
                color=UIConfig.get_color('TEXT_COLOR')
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
            color=UIConfig.get_color('TEXT_COLOR')
        )
        self.add_widget(title_label)
        
        # Create scrollable container for chart data
        scroll = ScrollView()
        chart_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8)
        chart_container.bind(minimum_height=chart_container.setter('height'))
        
        # Sort by date
        sorted_stats = sorted(stats.items())
        # Find maximum number of tasks completed in a single day
        max_value = max(stats.values()) if stats else 1
        
        # Get date and count from database
        for date, count in sorted_stats:
            # Create row for each date
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=15, spacing=10)
            
            # Date label
            date_label = Label(
                text=date, 
                size_hint_x=None, 
                width=100, 
                halign='right',
                font_size=12,
                color=UIConfig.get_color('TEXT_COLOR')
            )
            row.add_widget(date_label)
            
            # Progress bar container - arrange child layouts horizontally
            progress_container = BoxLayout(orientation='horizontal', size_hint_x=1)
            
            # Create visual bar using ProgressBar
            progress_bar = ProgressBar(
                max=max_value,
                value=count,  # count from database (stored in get_stats() function)
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
                color=UIConfig.get_color('TEXT_COLOR')
            )
            row.add_widget(count_label)
            
            chart_container.add_widget(row)
        
        # Add total summary section
        total_completed = sum(stats.values())
        total_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        total_row.add_widget(Label(text="--" * 50, size_hint_x=1, halign='center', color=UIConfig.get_color("TEXT_COLOR")))
        chart_container.add_widget(total_row)
        
        summary_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=35, spacing=10)
        summary_row.add_widget(Label(
            text="TOTAL", 
            size_hint_x=None, 
            width=100, 
            halign='right', 
            bold=True,
            color=UIConfig.get_color('TEXT_COLOR')
        ))
        summary_row.add_widget(Label(text="", size_hint_x=1))
        summary_row.add_widget(Label(
            text=f"{total_completed} task{'s' if total_completed != 1 else ''}", 
            size_hint_x=None, 
            width=80, 
            halign='left', 
            bold=True,
            color=UIConfig.get_color('TEXT_COLOR')
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