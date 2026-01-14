# branches/migrations/0005_seed_ghana_regions.py
from django.db import migrations


def seed_ghana_regions(apps, schema_editor):
    Country = apps.get_model("branches", "Country")
    Region = apps.get_model("branches", "Region")

    ghana, _ = Country.objects.get_or_create(
        code="GH",
        defaults={"name": "Ghana"},
    )

    region_names = [
        "Greater Accra",
        "Central",
        "Western",
        "Western North",
        "Eastern",
        "Ashanti",
        "Volta",
        "Oti",
        "Bono",
        "Bono East",
        "Ahafo",
        "Northern",
        "North East",
        "Savannah",
        "Upper East",
        "Upper West",
    ]

    for name in region_names:
        Region.objects.get_or_create(
            country=ghana,
            name=name,
            defaults={"code": None},
        )


def noop_reverse(apps, schema_editor):
    # Regions are immutable geography
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("branches", "0004_region_belt_alter_region_code_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_ghana_regions, noop_reverse),
    ]
