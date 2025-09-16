# Generated manually for OTP verification

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('generator', '0004_payment_suggestion'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='email_otp',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='email_otp_attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='email_otp_created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='phone_number',
            field=models.CharField(blank=True, help_text='Phone verification - Coming Soon!', max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='phone_otp',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='phone_otp_attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='phone_otp_created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='phone_verified',
            field=models.BooleanField(default=False),
        ),
    ]