from django.db import models
from django.core.validators import MinValueValidator

from model_utils import Choices

SERVER_STATUS = Choices(
    ('initial', 'initial'),
    ('in_progress', 'in_progress'),
    ('ready', 'ready'),
    ('finished', 'finished')
)


class Problem(models.Model):
    idx = models.PositiveSmallIntegerField()
    auth_key = models.UUIDField()


class Location(models.Model):
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        verbose_name='problem'
    )
    idx = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0)]
    )
    row = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0)],
        default=0
    )
    col = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0)],
        default=0
    )
    bike = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0)],
        default=0
    )


class Truck(models.Model):
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        verbose_name='problem'
    )
    idx = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0)],
        default=0
    )
    loc_row = models.PositiveSmallIntegerField(default=0)
    loc_col = models.PositiveSmallIntegerField(default=1)
    loc_idx = models.PositiveSmallIntegerField(default=0)
    bikes = models.PositiveSmallIntegerField(default=0)


class Score(models.Model):
    problem = models.OneToOneField(
        Problem,
        on_delete=models.CASCADE,
        verbose_name='problem'
    )
    status = models.CharField(
        choices=SERVER_STATUS,
        default=SERVER_STATUS.initial,
        max_length=20
    )
    score = models.FloatField(default=0.0)
