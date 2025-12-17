from django.core.management.base import BaseCommand
from decimal import Decimal
from jobs.models import ServiceType, ServicePricingRule


class Command(BaseCommand):
    help = "Seed flat pricing rules for non-print services"

    def handle(self, *args, **options):
        pricing_data = [
            ("EMAIL_SENDING", "5.00"),
            ("CV_PREPARATION", "30.00"),
            ("FORMS_FILLING", "50.00"),
            ("DOCUMENT_EDITING", "20.00"),
        ]

        created, skipped, missing = 0, 0, 0

        for code, price in pricing_data:
            try:
                service = ServiceType.objects.get(code=code)
            except ServiceType.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Missing ServiceType: {code}"))
                missing += 1
                continue

            obj, was_created = ServicePricingRule.objects.get_or_create(
                service_type=service,
                pricing_type="flat",
                paper_size=None,
                print_mode=None,
                color_mode=None,
                side_mode=None,
                defaults={
                    "unit_price": Decimal(price),
                    "is_active": True,
                },
            )

            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created flat rule: {service.code} → {price}"))
            else:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"Skipped (exists): {service.code}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Flat pricing seeding complete → Created: {created}, Skipped: {skipped}, Missing services: {missing}"
            )
        )
