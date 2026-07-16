from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CallHistory(models.Model):
    user1 = models.ForeignKey(User, related_name='calls_initiated', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='calls_received', on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True, help_text="Duration in seconds")

    def __str__(self):
        return f"Call between {self.user1} and {self.user2} at {self.start_time}"
