from django.contrib import admin
from .models import Announcement, ContractorRequest, Comment, Ticket, TicketMessage

admin.site.register(Announcement)
admin.site.register(ContractorRequest)
admin.site.register(Comment)
admin.site.register(Ticket)
admin.site.register(TicketMessage)
