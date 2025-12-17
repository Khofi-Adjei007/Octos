from django.core.management.base import BaseCommand
from decimal import Decimal
from jobs.models import ServiceType, ServicePricingRule


class Command(BaseCommand):
    help = "Seed service types and pricing rules for jobs"

    def handle(self, *args, **options):

        # ============================================================
        # SERVICE TYPES (FLAT / NON-PRINT SERVICES)
        # ============================================================
        services = [
            {
                "code": "EMAIL_SENDING",
                "name": "Email Sending",
                "category": "document_services",
                "is_quick": True,
            },
            {
                "code": "CV_PREPARATION",
                "name": "CV Preparation",
                "category": "document_services",
                "is_quick": True,
            },
            {
                "code": "DOCUMENT_EDITING",
                "name": "Document Editing",
                "category": "document_services",
                "is_quick": True,
            },
            {
                "code": "FORMS_FILLING",
                "name": "Forms & Filling",
                "category": "assisted_services",
                "is_quick": False,
            },

            {
                "code": "A4_PRINT",
                "name": "A4 Printing",
                "category": "document_printing",
                "is_quick": True,
            },
            {
                "code": "A3_PRINT",
                "name": "A3 Printing",
                "category": "document_printing",
                "is_quick": True,
            },
        ]

        for svc in services:
            obj, created = ServiceType.objects.get_or_create(
                code=svc["code"],
                defaults={
                    "name": svc["name"],
                    "category": svc["category"],
                    "is_quick": svc["is_quick"],
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created ServiceType: {obj.code}"))
            else:
                self.stdout.write(self.style.WARNING(f"ServiceType exists: {obj.code}"))

        # ============================================================
        # PRICING RULES — A4 / A3 PRINTOUT (VARIANT PRICING)
        # ============================================================
        pricing_data = [
            # ---------------- A4 PRINTOUT ----------------
            ("A4_PRINT", "A4", "printout", "bw", "single", "1.00"),
            ("A4_PRINT", "A4", "printout", "bw", "double", "1.50"),
            ("A4_PRINT", "A4", "printout", "color", "single", "2.00"),
            ("A4_PRINT", "A4", "printout", "color", "double", "3.00"),

            # ---------------- A3 PRINTOUT ----------------
            ("A3_PRINT", "A3", "printout", "bw", "single", "2.50"),
            ("A3_PRINT", "A3", "printout", "bw", "double", "3.50"),
            ("A3_PRINT", "A3", "printout", "color", "single", "3.50"),
            ("A3_PRINT", "A3", "printout", "color", "double", "5.00"),
        ]

        created, skipped = 0, 0

        for code, size, mode, color, side, price in pricing_data:
            try:
                service = ServiceType.objects.get(code=code)
            except ServiceType.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Missing ServiceType: {code}"))
                continue

            obj, was_created = ServicePricingRule.objects.get_or_create(
                service_type=service,
                paper_size=size,
                print_mode=mode,
                color_mode=color,
                side_mode=side,
                defaults={
                    "pricing_type": "variant",
                    "unit_price": Decimal(price),
                    "is_active": True,
                },
            )

            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created pricing rule: {obj}"))
            else:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"Skipped pricing rule: {obj}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Pricing seeding complete → Created: {created}, Skipped: {skipped}"
            )
        )
