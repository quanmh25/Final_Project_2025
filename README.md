
# 📋 Todo App – Task Management with Kivy

A cross-platform, customizable task management app built with **Python**, **Kivy**, and **SQLite**.  
The app allows you to **create**, **categorize**, **tag**, **schedule**, and **analyze** your daily tasks with an intuitive UI and dark/light theme support.

---

## 🚀 Features

- ✅ **Add/Edit/Delete Tasks**
- 🎯 **Mark Tasks as Completed or Pending**
- 📂 **Categories and Tags** for task grouping and filtering
- ⏰ **Set Deadlines** with date and optional time
- 📊 **Statistics Dashboard** with completion progress and charts
- 🌙 **Light/Dark Theme Toggle** (persisted across sessions)
- 🧩 **Modular Design** using Kivy's `ScreenManager`
- 💾 **SQLite Database** with automatic schema creation

---

## 🖥️ Screenshots

> *(Add screenshots here if available)*

---

## 🛠️ Tech Stack

- **Python 3**
- **Kivy** – UI framework
- **SQLite** – embedded database
- **Object-Oriented Design** – modular architecture

---

## 📂 Folder Structure

```
project/
│
├── models/
│   ├── category.py         # Category UI and logic
│   ├── custom_ui.py        # Custom buttons, inputs, and themes
│   ├── database.py         # SQLite DB operations
│   ├── deadline.py         # Deadline features and reminder logic
│   ├── stats_screen.py     # Statistics screen with charts
│   └── todo_screen.py      # Main screen for tasks
│
├── data/                   # App data folder (created automatically)
│   └── todo.db             # SQLite database
|  
│
├── main.py                 # App entry point and screen manager
└── README.md
```

---

## ⚙️ Installation & Run

### 📦 Requirements

- Python 3.7+
- Kivy (`pip install kivy`)
- Optionally: Kivy dependencies for your OS (e.g. `pygame`, `sdl2`, etc.)

### ▶️ Run the App

```bash
python main.py
```

> The app will create the `data/todo.db` database and theme settings on first run.

---

## 💡 Customization

- Modify `UIConfig` in `models/custom_ui.py` or `models/category.py` to tweak colors, fonts, sizes.
- Add new task types, priorities, or screen tabs via `ScreenManager` in `main.py`.

---

## 🗂️ Persistence

All data is stored in `data/todo.db` using **SQLite**.  
Theme preference is saved to `data/theme.json`.

---

## 📘 License

This project is open-source and licensed under the MIT License.

