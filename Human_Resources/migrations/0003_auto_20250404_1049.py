# Human_Resources/migrations/000X_auto_YYYYMMDD_HHMM.py
from django.db import migrations

def populate_roles(apps, schema_editor):
    Role = apps.get_model('Human_Resources', 'Role')
    roles = [
        ('branch_manager', 'Branch Manager'),
        ('regional_hr_manager', 'Regional Human Resource Manager'),
        ('general_attendant', 'General Attendant'),
        ('cashier', 'Cashier'),
        ('graphic_designer', 'Graphic Designer'),
        ('large_format_machine_operator', 'Large Format/Machine Operator'),
        ('zonal_delivery_dispatch_rider', 'Zonal Delivery/Dispatch Rider'),
        ('field_officer', 'Field Officer'),
        ('cleaner', 'Cleaner'),
        ('secretary', 'Secretary'),
        ('marketer', 'Marketer'),
        ('accountant', 'Accountant'),
        ('it_support_technician', 'IT Support/Technician'),
        ('inventory_manager', 'Inventory Manager'),
        ('quality_control_inspector', 'Quality Control Inspector'),
    ]
    for name, description in roles:
        Role.objects.get_or_create(name=name, defaults={'description': description})

class Migration(migrations.Migration):
    dependencies = [
        ('Human_Resources', '0001_initial'),  # Adjust based on your last migration
    ]

    operations = [
        migrations.RunPython(populate_roles),
    ]