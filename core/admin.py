from django.contrib import admin
from .models import User, Announcement, Comment, Ticket

admin.site.register(User)
admin.site.register(Announcement)
admin.site.register(Comment)
admin.site.register(Ticket)
