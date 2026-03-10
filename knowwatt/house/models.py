from django.db import models
import uuid
from django.conf import settings


class House(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    house_name = models.CharField(max_length=255)
    address = models.TextField()
    lat = models.FloatField(null=True, blank=True)
    long = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'house'
        verbose_name = 'House'
        verbose_name_plural = 'Houses'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.house_name} ({self.id})"


class HouseMember(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('member', 'Member'),
        ('guest', 'guest'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    house = models.ForeignKey(
        House,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='house_memberships'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'house_member'
        verbose_name = 'House Member'
        verbose_name_plural = 'House Members'
        unique_together = ['house', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.house.house_name} ({self.role})"
