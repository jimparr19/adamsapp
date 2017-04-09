import os
from django.db import models


class DataFile(models.Model):
    raw_datafile = models.FileField(upload_to='raw_data/%Y/%m/%d')
    processed_datafile = models.FileField(upload_to='processed_data/%Y/%m/%d')

    start_time = models.FloatField(default="-inf")
    finish_time = models.FloatField(default="inf")

    def __str__(self):
        return os.path.basename(self.raw_datafile.name)


class Session(models.Model):
    start_time = models.DateTimeField(blank=True, null=True)
    finish_time = models.DateTimeField(blank=True, null=True)
    start_time_unix = models.FloatField(blank=True, null=True)
    finish_time_unix = models.FloatField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    left_hand_file = models.ManyToManyField(DataFile, blank=True, related_name="left_hand")
    right_hand_file = models.ManyToManyField(DataFile, blank=True, related_name="right_hand")
    notes = models.TextField(default="", blank=True, null=True)
    view_div = models.TextField(default=None, blank=True, null=True)
    view_script = models.TextField(default=None, blank=True, null=True)
    activity_ratio = models.FloatField(blank=True, null=True)

