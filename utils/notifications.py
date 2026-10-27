from abc import ABC, abstractmethod
import logging
import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class BaseNotificationProvider(ABC):
    """Abstract base class for all notification transport layers."""
    @abstractmethod
    def send(self, message: str, priority: str) -> bool:
        pass

class ConsoleProvider(BaseNotificationProvider):
    """Standard system logs for notifications."""
    def send(self, message: str, priority: str) -> bool:
        print(f"[CONSOLE ALERT] [{priority}] {message}")
        return True

class MockWhatsAppProvider(BaseNotificationProvider):
    """Simulates sending a WhatsApp message."""
    def send(self, message: str, priority: str) -> bool:
        logger.info(f"[SIMULATED WHATSAPP] Sending to farmer: {message} (Priority: {priority})")
        return True

class MockSmsProvider(BaseNotificationProvider):
    """Simulates sending an SMS message."""
    def send(self, message: str, priority: str) -> bool:
        logger.info(f"[SIMULATED SMS] Sending to farmer: {message} (Priority: {priority})")
        return True

class NotificationEngine:
    """
    Advanced notification system that delegates alerts to multiple active providers.
    """
    def __init__(self):
        # Default providers
        self.providers: Dict[str, BaseNotificationProvider] = {
            "console": ConsoleProvider(),
            "whatsapp": MockWhatsAppProvider(),
            "sms": MockSmsProvider(),
        }
        self.active_providers = ["console"]

    def enable_provider(self, provider_name: str):
        if provider_name in self.providers:
            if provider_name not in self.active_providers:
                self.active_providers.append(provider_name)
                logger.info(f"Enabled notification provider: {provider_name}")

    def disable_provider(self, provider_name: str):
        if provider_name in self.active_providers:
            self.active_providers.remove(provider_name)
            logger.info(f"Disabled notification provider: {provider_name}")

    def send_alert(self, message: str, priority: str = "MEDIUM"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        full_message = f"[{timestamp}] {message}"

        results = []
        for provider_name in self.active_providers:
            provider = self.providers.get(provider_name)
            if provider:
                success = provider.send(full_message, priority)
                results.append(success)

        return f"Notification sent via {', '.join(self.active_providers)}"

    def get_all_notifications(self):
        """
        Maintain compatibility with old UI:
        since we now use external providers, this would ideally query a DB.
        For now, we'll just return a mock list or a 'See logs' message.
        """
        return [{"timestamp": "N/A", "message": "Notifications now sent via active providers. Check logs."}]

    def clear_notifications(self):
        """No-op in the new pluggable architecture."""
        pass

# Singleton instance
notifier = NotificationEngine()
