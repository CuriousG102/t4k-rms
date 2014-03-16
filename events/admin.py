from django.contrib import admin
from events.models import Event, Participant


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 3

class EventAdmin(admin.ModelAdmin):
    inlines = (ParticipantInline,)

# Register your models here.

admin.site.register(Event, EventAdmin)

