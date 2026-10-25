import datetime

class NotificationEngine:
    """Simulates a notification system for proactive alerts."""
    def __init__(self):
        self.notifications = []

    def send_alert(self, message: str, priority: str = "MEDIUM"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        alert = {"timestamp": timestamp, "message": message, "priority": priority}
        self.notifications.append(alert)
        return f"Notification Sent [{priority}]: {message}"

    def get_all_notifications(self):
        return self.notifications

    def clear_notifications(self):
        self.notifications = []

# Singleton instance
notifier = NotificationEngine()
