import time
from collections import deque

class TokenUsageTracker:
    def __init__(self, limit_per_minute):
        self.limit = limit_per_minute
        self.usage_window = deque()  # Stores (timestamp, tokens_used)

    def add_usage(self, tokens_used: int):
        now = time.time()
        self.usage_window.append((now, tokens_used))
        self.cleanup(now)

    def get_usage_total(self):
        now = time.time()
        self.cleanup(now)
        return sum(tokens for timestamp, tokens in self.usage_window)

    def cleanup(self, current_time):
        while self.usage_window and current_time - self.usage_window[0][0] > 60:
            self.usage_window.popleft()

    def can_process(self, tokens_needed: int):
        return self.get_usage_total() + tokens_needed <= self.limit