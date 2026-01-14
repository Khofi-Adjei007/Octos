# branches/migrations/0005_assign_regions_to_belts.py
from django.db import migrations


def assign_regions_to_belts(apps, schema_editor):
    Region = apps.get_model("branches", "Region")
    Belt = apps.get_model("Human_Resources", "Belt")

    # Fetch belts (fail fast if missing)
    try:
        south = Belt.objects.get(code="SOUTH")
        mid = Belt.objects.get(code="MID")
        north = Belt.objects.get(code="NORTH")
    except Belt.DoesNotExist as e:
        raise RuntimeError("Required belts are missing. Run belt seeding migration first.") from e

    # Explicit region → belt mapping
    REGION_BELT_MAP = {
        # Southern Belt
        "Greater Accra": south,
        "Central": south,
        "Western": south,
        "Western North": south,
        "Volta": south,
        "Oti": south,

        # Middle Belt
        "Eastern": mid,
        "Ashanti": mid,
        "Bono": mid,
        "Bono East": mid,
        "Ahafo": mid,

        # Northern Belt
        "Northern": north,
        "North East": north,
        "Savannah": north,
        "Upper East": north,
        "Upper West": north,
    }

    for region_name, belt in REGION_BELT_MAP.items():
        updated = Region.objects.filter(name=region_name).update(belt=belt)
        if updated == 0:
            raise RuntimeError(
                f"Region '{region_name}' not found. "
                "Region data must exist before assigning belts."
            )


def noop_reverse(apps, schema_editor):
    """
    Do not unassign belts on reverse.
    This is foundational geographic data.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
    ("branches", "0005_seed_ghana_regions"),
    ("Human_Resources", "0010_seed_belts"),
    ]


    operations = [
        migrations.RunPython(assign_regions_to_belts, noop_reverse),
    ]
