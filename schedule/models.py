from django.db import models


class Discipline(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Country(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)
    continent = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'countries'


class Venue(models.Model):
    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.short_name or self.name

    class Meta:
        ordering = ['name']


class Event(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('RUNNING', 'Running'),
        ('FINISHED', 'Finished'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.CharField(max_length=50, primary_key=True)
    discipline = models.ForeignKey(
        Discipline, on_delete=models.CASCADE, related_name='events'
    )
    event_name = models.CharField(max_length=200)
    unit_name = models.CharField(max_length=200, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    venue = models.ForeignKey(
        Venue, on_delete=models.SET_NULL, null=True, related_name='events'
    )
    location = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='SCHEDULED'
    )
    is_live = models.BooleanField(default=False)
    is_medal_event = models.BooleanField(default=False)
    competitors_json = models.JSONField(default=list, blank=True)
    competitors = models.ManyToManyField(
        Country, related_name='events', blank=True
    )
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.discipline.name}: {self.event_name} - {self.unit_name}"

    class Meta:
        ordering = ['start_time']
