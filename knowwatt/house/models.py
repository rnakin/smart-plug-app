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
    emoji = models.CharField(max_length=10, default='🏠')
    # deleted = models.BooleanField(default=False)
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
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('guest', 'Guest'),
    ]
    
    # Role permissions mapping
    PERMISSIONS = {
        'owner': {
            'can_create_house': True,
            'can_edit_house': True,
            'can_delete_house': True,
            'can_manage_members': True,
            'can_remove_owner': False,
            'can_control_devices': True,
            'can_view_devices': True,
            'can_view_members': True,
        },
        'admin': {
            'can_create_house': False,
            'can_edit_house': False,
            'can_delete_house': False,
            'can_manage_members': True,
            'can_remove_owner': False,
            'can_remove_admin': False,
            'can_control_devices': True,
            'can_view_devices': True,
            'can_view_members': True,
        },
        'member': {
            'can_create_house': False,
            'can_edit_house': False,
            'can_delete_house': False,
            'can_manage_members': False,
            'can_remove_owner': False,
            'can_control_devices': True,
            'can_view_devices': True,
            'can_view_members': True,
        },
        'guest': {
            'can_create_house': False,
            'can_edit_house': False,
            'can_delete_house': False,
            'can_manage_members': False,
            'can_control_devices': False,
            'can_view_devices': True,
            'can_view_members': True,
        },
    }
    
    @classmethod
    def has_permission(cls, membership, permission):
        """Check if membership has a specific permission"""
        if not membership:
            return False
        role_perms = cls.PERMISSIONS.get(membership.role, {})
        return role_perms.get(permission, False)
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    house = models.ForeignKey( House, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,related_name='house_memberships',null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'house_member'
        verbose_name = 'House Member'
        verbose_name_plural = 'House Members'
        unique_together = ['house', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.house.house_name} ({self.role})"
