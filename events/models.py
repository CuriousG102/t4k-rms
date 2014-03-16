from django.db import models
from datetime import datetime
from riders.models import Teammate

# Create your models here.
class Event(models.Model):
    name = models.CharField('Name of Event', max_length = 128)
    description = models.TextField('description')
    participants = models.ManyToManyField(Teammate, through = 'Participant', related_name = 'people participating in event')
    time = models.DateTimeField('Day and Time of Event')
    hosts = models.ManyToManyField(Teammate, related_name = 'people hosting event')

    def __unicode__(self):
        return self.name

class Participant(models.Model):
    teammate = models.ForeignKey(Teammate)
    event = models.ForeignKey(Event)
    date_joined = models.DateTimeField(auto_now_add = True)
    role = models.CharField('Role in Event', max_length = 128)
    attended = models.BooleanField('attended')

    def __unicode__(self):
        return self.teammate.__unicode__()
