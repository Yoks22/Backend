from datetime import datetime
from zoneinfo import ZoneInfo
import threading
import time

IST = ZoneInfo("Asia/Kolkata")

def start_scheduler(app, client):
    def loop():
        last_run_date = None
        print("✓ Scheduler background thread is active and monitoring...")

        while True:
            try:
                now = datetime.now(IST)

                is_saturday = now.weekday() == 5
                is_target_time = now.hour == 10 and now.minute == 0
                not_yet_run_today = last_run_date != now.date()

                if is_saturday and is_target_time and not_yet_run_today:
                    print(f"=== SATURDAY AUTO-SYNC TRIGGERED @ {now} ===")

                    with app.app_context():
                        success, message, details = manual_sync(client)

                    if success:
                        last_run_date = now.date()
                        print("Auto-sync successful")
                    else:
                        print("Auto-sync failed")

                    print("=== SATURDAY AUTO-SYNC FINISHED ===")

                time.sleep(30)  # check twice per minute for safety

            except Exception as e:
                import traceback
                traceback.print_exc()
                time.sleep(300)

    threading.Thread(target=loop, daemon=True).start()
