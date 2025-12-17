# jobs/api/serializers.py
from rest_framework import serializers
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

Job = apps.get_model("jobs", "Job")
JobRecord = apps.get_model("jobs", "JobRecord")
JobAttachment = apps.get_model("jobs", "JobAttachment")
ServiceType = apps.get_model("jobs", "ServiceType")
ServicePricingRule = apps.get_model("jobs", "ServicePricingRule")

from jobs.services import job_service


# --------------------------------------------------
# EXISTING SERIALIZERS (UNCHANGED)
# --------------------------------------------------

class JobAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = JobAttachment
        fields = ["id", "file", "note", "uploaded_by", "created_at"]
        read_only_fields = ["id", "uploaded_by", "created_at"]


class JobRecordSerializer(serializers.ModelSerializer):
    attachments = JobAttachmentSerializer(many=True, read_only=True)
    performed_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = JobRecord
        fields = [
            "id", "job", "performed_by", "time_start", "time_end",
            "quantity_produced", "notes", "issues", "attachments", "created_at"
        ]
        read_only_fields = ["id", "attachments", "created_at"]

    def validate(self, data):
        ts = data.get("time_start")
        te = data.get("time_end")
        if ts and te and te < ts:
            raise serializers.ValidationError("time_end cannot be before time_start")
        return data


class JobSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Job
        fields = [
            "id","branch","service","customer_name","customer_phone","description",
            "quantity","price","unit_price","total_amount","deposit_amount",
            "expected_minutes_per_unit","priority","type","status",
            "queue_position","expected_ready_at","completed_at","created_by","created_at",
        ]
        read_only_fields = [
            "id","unit_price","total_amount","queue_position",
            "expected_ready_at","completed_at","created_at","created_by","status"
        ]

    def _infer_branch_from_user(self, user):
        try:
            emp = getattr(user, "employee", None)
            if emp and getattr(emp, "branch", None):
                return emp.branch
        except Exception:
            pass
        try:
            if getattr(user, "branch", None):
                return getattr(user, "branch")
        except Exception:
            pass
        return None

    def create(self, validated_data):
        request = self.context.get("request", None)
        user = request.user if request and request.user.is_authenticated else None

        if "branch" not in validated_data or not validated_data.get("branch"):
            branch_obj = self._infer_branch_from_user(user) if user else None
            if branch_obj is None:
                raise serializers.ValidationError(
                    "branch is required (no assigned branch found for user)."
                )
            validated_data["branch"] = branch_obj

        job_type = validated_data.get("type")
        if job_type == "instant":
            branch_id = validated_data["branch"].pk
            service_id = validated_data["service"].pk
            return job_service.create_instant_job(
                branch_id=branch_id,
                service_id=service_id,
                quantity=validated_data.get("quantity", 1),
                created_by=user,
                customer_name=validated_data.get("customer_name"),
                customer_phone=validated_data.get("customer_phone"),
                deposit=validated_data.get("deposit_amount", 0),
                description=validated_data.get("description", ""),
            )

        with transaction.atomic():
            data = dict(validated_data)
            svc = data.get("service")
            unit_price = getattr(svc, "price", None) or data.get("price") or Decimal("0.00")
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

            instance = Job.objects.create(**data)

            try:
                job_service.attach_job_to_daysheet_idempotent(
                    instance, user=user, now=timezone.now()
                )
            except Exception:
                pass

            return instance


# --------------------------------------------------
# NEW SERIALIZERS (FOR UI SERVICE + PRICING)
# --------------------------------------------------

class ServiceTypeSerializer(serializers.ModelSerializer):
    is_print_service = serializers.SerializerMethodField()

    class Meta:
        model = ServiceType
        fields = [
            "id",
            "code",
            "name",
            "category",
            "is_quick",
            "is_print_service",
        ]

    def get_is_print_service(self, obj):
        return obj.code in {"A4_PRINT", "A3_PRINT"}


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
