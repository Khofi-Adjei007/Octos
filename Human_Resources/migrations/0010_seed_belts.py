# Human_Resources/migrations/0010_seed_belts.py
from django.db import migrations


def seed_belts(apps, schema_editor):
    Belt = apps.get_model("Human_Resources", "Belt")

    belts = [
        {
            "code": "SOUTH",
            "name": "Southern Belt",
            "order": 1,
        },
        {
            "code": "MID",
            "name": "Middle Belt",
            "order": 2,
        },
        {
            "code": "NORTH",
            "name": "Northern Belt",
            "order": 3,
        },
    ]

    for belt_data in belts:
        Belt.objects.get_or_create(
            code=belt_data["code"],
            defaults={
                "name": belt_data["name"],
                "order": belt_data["order"],
            },
        )


def noop_reverse(apps, schema_editor):
    """
    Belts are immutable global references.
    We intentionally do NOT delete them on reverse.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("Human_Resources", "0009_belt_hrresponsibility_hrscope_hrscopeassignment_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_belts, noop_reverse),
    ]
