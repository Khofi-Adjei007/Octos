# branches/migrations/0007_make_region_belt_required.py
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("branches", "0006_assign_regions_to_belts"),
    ]

    operations = [
        migrations.AlterField(
            model_name="region",
            name="belt",
            field=models.ForeignKey(
                to="Human_Resources.belt",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="regions",
                help_text="Geographic belt this region belongs to",
                null=False,
                blank=False,
            ),
        ),
    ]
