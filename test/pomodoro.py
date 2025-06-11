import threading
import time
from datetime import datetime, timedelta
from plyer import notification


class ReminderApp:
    def __init__(self):
        self.pomodoro_work_time = 25 * 60  # 25 phút làm việc (tính bằng giây)
        self.pomodoro_break_time = 5 * 60  # 5 phút nghỉ
        self.is_running = False
        self.deadlines = {}  # Lưu các deadline: {tên: thời gian}

    def start_pomodoro(self):
        """Bắt đầu một phiên Pomodoro"""
        self.is_running = True
        print("Bắt đầu Pomodoro: 25 phút làm việc!")
        
        # Đếm ngược thời gian làm việc
        self.countdown(self.pomodoro_work_time, "Hết thời gian làm việc! Nghỉ 5 phút.")
        
        if self.is_running:
            print("Bắt đầu nghỉ: 5 phút!")
            self.countdown(self.pomodoro_break_time, "Hết thời gian nghỉ! Tiếp tục làm việc.")

    def countdown(self, seconds, message):
        """Hàm đếm ngược với thông báo khi hết thời gian"""
        while seconds > 0 and self.is_running:
            mins, secs = divmod(seconds, 60)
            print(f"Thời gian còn lại: {mins:02d}:{secs:02d}", end="\r")
            time.sleep(1)
            seconds -= 1
        if self.is_running:
            self.notify(message)

    def stop_pomodoro(self):
        """Dừng Pomodoro"""
        self.is_running = False
        print("\nPomodoro đã dừng.")

    def set_deadline(self, name, deadline_time):
        """Đặt deadline: deadline_time là datetime object"""
        self.deadlines[name] = deadline_time
        print(f"Đã đặt deadline '{name}' vào {deadline_time}")
        self.check_deadline(name)

    def check_deadline(self, name):
        """Kiểm tra deadline và thông báo khi còn 24 giờ"""
        deadline = self.deadlines.get(name)
        if not deadline:
            return
        
        def _check():
            while True:
                now = datetime.now()
                time_left = (deadline - now).total_seconds()
                
                # Nếu còn dưới 24 giờ, thông báo
                if 0 < time_left <= 24 * 3600:
                    self.notify(f"Cảnh báo: Deadline '{name}' còn dưới 24 giờ!")
                    break
                elif time_left <= 0:
                    self.notify(f"Deadline '{name}' đã hết hạn!")
                    break
                time.sleep(60)  # Kiểm tra mỗi phút
        
        threading.Thread(target=_check, daemon=True).start()

    def notify(self, message):
        """Gửi thông báo"""
        try:
            notification.notify(
                title="Nhắc nhở",
                message=message,
                app_name="ReminderApp",
                timeout=5
            )
        except Exception as e:
            print(f"Thông báo: {message} (Lỗi: {e})")

# Ví dụ sử dụng
if __name__ == "__main__":
    app = ReminderApp()

    # Chạy Pomodoro
    pomodoro_thread = threading.Thread(target=app.start_pomodoro)
    pomodoro_thread.start()

    # Đặt một deadline ví dụ (hết hạn sau 25 giờ từ bây giờ)
    deadline_time = datetime.now() + timedelta(hours=25)
    app.set_deadline("Gửi báo cáo", deadline_time)

    # Để kiểm tra, bạn có thể dừng Pomodoro sau 10 giây
    time.sleep(10)
    app.stop_pomodoro()