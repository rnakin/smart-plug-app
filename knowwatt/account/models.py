from django.db import models

class UserPreference(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='preferences')
    last_house_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'user_preference'
