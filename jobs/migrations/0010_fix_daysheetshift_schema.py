from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0009_alter_job_service"),
    ]

    operations = [
        migrations.AddField(
            model_name="daysheetshift",
            name="status",
            field=models.CharField(
                max_length=24,
                choices=[
                    ("shift_open", "Open"),
                    ("shift_closed", "Closed"),
                    ("shift_auto_closed", "Auto Closed"),
                    ("locked", "Locked"),
                ],
                default="shift_open",
            ),
        ),
    ]
