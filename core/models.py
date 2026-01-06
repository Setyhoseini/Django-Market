from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True, null=True)

    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('contractor', 'Contractor'),
        ('support', 'Support'),
        ('admin', 'Admin'),
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='customer'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} ({self.role})"


class Announcement(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    creator = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='announcements'
    )
    assigned_to = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_jobs'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey('User', on_delete=models.CASCADE)
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1–5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.email}"


class Ticket(models.Model):
    creator = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
