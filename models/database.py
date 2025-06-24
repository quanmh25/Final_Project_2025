import sqlite3
import traceback
from datetime import datetime


# =============================================================================
# DATABASE CLASS
# =============================================================================

class TodoDB:
    """Database manager for Todo application."""
    
    def __init__(self):
        """Initialize database connection and create tables."""
        try:
            self.conn = sqlite3.connect("data/todo.db")
            self.create_table()
            self.create_deadline_table()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise

    def create_table(self):
        """Create main tasks table."""
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

    def create_deadline_table(self):
        """Create deadlines table and add deadline columns to tasks table."""
        try:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS task_deadlines
                                (task_id INTEGER,
                                deadline_date TEXT NOT NULL,
                                deadline_time TEXT,
                                FOREIGN KEY (task_id) REFERENCES tasks(id))''')
            
            # Add deadline columns to tasks table if they don't exist
            for column in ['deadline_date', 'deadline_time', 'priority']:
                try:
                    self.conn.execute(f'ALTER TABLE tasks ADD COLUMN {column} TEXT')
                except sqlite3.OperationalError:
                    pass  # Column already exists
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating deadline table: {e}")
            raise

    def add_task(self, title):
        """Add a new task to the database."""
        try:
            if not title or not title.strip():
                raise ValueError("Task title cannot be empty")
            
            today = datetime.today().strftime('%Y-%m-%d')  # Get current date
            self.conn.execute("INSERT INTO tasks (title, done, date) VALUES (?, 0, ?)", 
                            (title.strip(), today))
            self.conn.commit()
            return True
        except (sqlite3.Error, ValueError) as e:
            print(f"Error adding task: {e}")
            return False
        
    def get_tasks(self, filter_status='all'):
        """Get list of tasks based on filter status."""
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

    def mark_done(self, task_id, done):
        """Mark task as completed or pending."""
        try:
            self.conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (done, task_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error marking task: {e}")
            return False

    def delete_task(self, task_id):
        """Delete a task from the database."""
        try:
            self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting task: {e}")
            return False

    def get_stats(self):
        """Get statistics of completed tasks by date."""
        try:
            # Query database to get completion statistics by date
            cursor = self.conn.execute("SELECT date, COUNT(*) FROM tasks WHERE done = 1 GROUP BY date ORDER BY date")
            return dict(cursor.fetchall())
        except sqlite3.Error as e:
            print(f"Error getting stats: {e}")
            return {}

    def get_task_summary(self):
        """Get summary of total, completed, and pending tasks."""
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
        """Close database connection."""
        if self.conn:
            self.conn.close()