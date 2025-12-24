from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from django.db import transaction
import logging

from jobs.models import (
    Job,
    JobRecord,
    JobAttachment,
    ServiceType,
    ServicePricingRule,
)

from jobs.services import job_service

logger = logging.getLogger(__name__)

User = get_user_model()


# ==================================================
# ATTACHMENTS
# ==================================================

class JobAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = JobAttachment
        fields = ["id", "file", "note", "uploaded_by", "created_at"]
        read_only_fields = ["id", "uploaded_by", "created_at"]


# ==================================================
# JOB RECORDS
# ==================================================

class JobRecordSerializer(serializers.ModelSerializer):
    attachments = JobAttachmentSerializer(many=True, read_only=True)
    performed_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = JobRecord
        fields = [
            "id",
            "job",
            "performed_by",
            "time_start",
            "time_end",
            "quantity_produced",
            "notes",
            "issues",
            "attachments",
            "created_at",
        ]
        read_only_fields = ["id", "attachments", "created_at"]

    def validate(self, data):
        ts = data.get("time_start")
        te = data.get("time_end")
        if ts and te and te < ts:
            raise serializers.ValidationError(
                "time_end cannot be before time_start"
            )
        return data


# ==================================================
# JOBS
# ==================================================

class JobSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    # 🔑 CRITICAL: Explicit FK resolution
    service = serializers.PrimaryKeyRelatedField(
        queryset=ServiceType.objects.all()
    )

    # write-only variant fields (NOT model fields)
    paper_size = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )
    print_mode = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )
    color_mode = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )
    side_mode = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )
    customer_name = serializers.CharField(
    required=False,
    allow_blank=True,
    default="",
)



    class Meta:
        model = Job
        fields = [
            "id",
            "branch",
            "service",
            "customer_name",
            "customer_phone",
            "description",
            "quantity",

            # pricing
            "price",
            "unit_price",
            "total_amount",
            "deposit_amount",

            # variant context (write-only)
            "paper_size",
            "print_mode",
            "color_mode",
            "side_mode",

            # metadata
            "expected_minutes_per_unit",
            "priority",
            "type",
            "status",
            "queue_position",
            "expected_ready_at",
            "completed_at",
            "created_by",
            "created_at",
        ]

    # -------------------------------
    # helpers
    # -------------------------------

    def _infer_branch_from_user(self, user):
        try:
            emp = getattr(user, "employee", None)
            if emp and getattr(emp, "branch", None):
                return emp.branch
        except Exception:
            pass

        try:
            if getattr(user, "branch", None):
                return user.branch
        except Exception:
            pass

        return None

    def _normalize_variant(self, value):
        return value if value not in ("", None) else None

    # -------------------------------
    # create
    # -------------------------------

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None

        if not validated_data.get("branch"):
            branch = self._infer_branch_from_user(user) if user else None
            if not branch:
                raise serializers.ValidationError(
                    "branch is required (no assigned branch found for user)."
                )
            validated_data["branch"] = branch

        job_type = validated_data.get("type") or "queued"


        # ----------------------------------
        # INSTANT (QUICK RECORD) JOB
        # ----------------------------------
        if job_type == "instant":
            service = validated_data.get("service")
            if not service:
                raise serializers.ValidationError("Service is required.")

            return job_service.create_instant_job(
                branch_id=validated_data["branch"].pk,
                service_id=service.pk,
                quantity=validated_data.get("quantity", 1),
                created_by=user,
                customer_name=validated_data.get("customer_name") or "",
                customer_phone=validated_data.get("customer_phone") or "",
                deposit=validated_data.get("deposit_amount", 0),
                description=validated_data.get("description", ""),
                paper_size=self._normalize_variant(validated_data.get("paper_size")),
                print_mode=self._normalize_variant(validated_data.get("print_mode")),
                color_mode=self._normalize_variant(validated_data.get("color_mode")),
                side_mode=self._normalize_variant(validated_data.get("side_mode")),
)


        # ----------------------------------
        # NON-INSTANT (PROCESS / QUEUED) JOB
        # ----------------------------------
        with transaction.atomic():
            data = dict(validated_data)

            # remove non-model fields
            data.pop("paper_size", None)
            data.pop("print_mode", None)
            data.pop("color_mode", None)
            data.pop("side_mode", None)


            svc = data.get("service")
            unit_price = (
                getattr(svc, "price", None)
                or data.get("price")
                or Decimal("0.00")
            )
            unit_price = Decimal(str(unit_price))

            qty = int(data.get("quantity", 1))
            deposit = Decimal(data.get("deposit_amount", 0))
            total = (unit_price * qty) - deposit
            if total < 0:
                total = Decimal("0.00")

            data["unit_price"] = unit_price
            data["total_amount"] = total.quantize(Decimal("0.01"))

            if user:
                data["created_by"] = user

            job = Job.objects.create(**data)

            try:
                job_service.attach_job_to_daysheet_idempotent(
                    job, user=user, now=timezone.now()
                )
            except Exception:
                logger.exception("Failed to attach job to daysheet")

            return job


# ==================================================
# PRICING RULES (READ-ONLY)
# ==================================================

class ServicePricingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePricingRule
        fields = [
            "pricing_type",
            "paper_size",
            "print_mode",
            "color_mode",
            "side_mode",
            "unit_price",
        ]


# ==================================================
# SERVICE TYPES (UI, WITH PRICING)
# ==================================================

class ServiceTypeSerializer(serializers.ModelSerializer):
    is_print_service = serializers.SerializerMethodField()
    pricing_rules = ServicePricingRuleSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = ServiceType
        fields = [
            "id",
            "code",
            "name",
            "category",
            "is_quick",
            "price",
            "is_print_service",
            "pricing_rules",
        ]

    def get_is_print_service(self, obj):
        return obj.code in {"A4_PRINT", "A3_PRINT"}
