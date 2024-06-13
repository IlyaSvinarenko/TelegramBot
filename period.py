import time
from datetime import datetime
import threading

def log_current_time(interval_seconds):
    while True:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(current_time)
        time.sleep(interval_seconds)

time_thread = threading.Thread(target=log_current_time, args=(10,))
time_thread.start()