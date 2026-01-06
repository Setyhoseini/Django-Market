# core/models.py
from django.conf import settings
from django.db import models

class Announcement(models.Model):
    STATUS_OPEN = "open"
    STATUS_ASSIGNED = "assigned"
    STATUS_DONE_REQUESTED = "done_requested"   # contractor marked done
    STATUS_DONE_CONFIRMED = "done_confirmed"   # customer confirmed
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_ASSIGNED, "Assigned"),
        (STATUS_DONE_REQUESTED, "Done Requested"),
        (STATUS_DONE_CONFIRMED, "Done Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="announcements", on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="assigned_announcements",
                                    on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


class ContractorRequest(models.Model):
    announcement = models.ForeignKey(Announcement, related_name="contractor_requests", on_delete=models.CASCADE)
    contractor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="contractor_requests", on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled = models.BooleanField(default=False)

    class Meta:
        unique_together = ("announcement", "contractor")

    def __str__(self):
        return f"Request by {self.contractor} for {self.announcement_id}"


class Comment(models.Model):
    announcement = models.ForeignKey(Announcement, related_name="comments", on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="comments", on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not (1 <= self.rating <= 5):
            raise ValueError("rating must be 1..5")
        super().save(*args, **kwargs)


class Ticket(models.Model):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [(STATUS_OPEN, "Open"), (STATUS_CLOSED, "Closed")]

    title = models.CharField(max_length=255)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="tickets", on_delete=models.CASCADE)
    announcement = models.ForeignKey(Announcement, related_name="tickets", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket #{self.pk}: {self.title}"


class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="ticket_messages", on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.pk} on Ticket {self.ticket_id}"
