import threading
import time
from datetime import datetime


def start_scheduler(app, client, interval_hours=None):
    """
    Background scheduler that checks every minute if it's Saturday at midnight.
    """

    def loop():
        # Keep track of the last date a sync was performed today
        last_run_date = None

        print("✓ Scheduler background thread is active and monitoring...")

        while True:
            try:
                now = datetime.now()

                # Logic: Is it Saturday? Is it the 00:00 hour (Midnight)? Have we run it yet today?
                is_saturday = now.weekday() == 5  # 5 = Saturday
                is_midnight_hour = now.hour == 0
                not_yet_run_today = last_run_date != now.date()

                if is_saturday and is_midnight_hour and not_yet_run_today:
                    print(f'=== SATURDAY AUTO-SYNC TRIGGERED: {now.strftime("%Y-%m-%d %H:%M:%S")} ===')

                    with app.app_context():
                        # We use the manual_sync function logic to perform the work
                        success, message, details = manual_sync(client)

                        if success:
                            last_run_date = now.date()  # Mark today as finished
                            print(f"Auto-sync successful: {message}")
                        else:
                            print(f"Auto-sync failed: {message}")

                    print('=== SATURDAY AUTO-SYNC FINISHED ===')

                # IMPORTANT: Wait 60 seconds before checking the clock again
                time.sleep(60)

            except Exception as e:
                print(f"Scheduler Error: {e}")
                time.sleep(300)  # Wait 5 minutes if there is a crash before restarting loop

    # Daemon=True ensures the thread stops when you stop the Flask server
    t = threading.Thread(target=loop, daemon=True)
    t.start()


def manual_sync(client):
    """
    Manual sync logic used by both the API and the Scheduler
    """
    try:
        res = client.sync_all()
        return True, 'Sync completed', res
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e), None