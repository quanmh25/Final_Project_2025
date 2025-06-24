import os
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