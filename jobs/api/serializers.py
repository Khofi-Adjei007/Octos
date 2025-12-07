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

from jobs.services import job_service

class JobAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = JobAttachment
        fields = ["id", "file", "note", "uploaded_by", "created_at"]
        read_only_fields = ["id", "uploaded_by", "created_at"]


class JobRecordSerializer(serializers.ModelSerializer):
    attachments = JobAttachmentSerializer(many=True, read_only=True)
    performed_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)

    class Meta:
        model = JobRecord
        fields = [
            "id", "job", "performed_by", "time_start", "time_end",
            "quantity_produced", "notes", "issues", "attachments", "created_at"
        ]
        read_only_fields = ["id", "attachments", "created_at"]

    def validate(self, data):
        # ensure time_end >= time_start when provided
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
        read_only_fields = ["id","unit_price","total_amount","queue_position","expected_ready_at","completed_at","created_at","created_by","status"]

    def validate(self, data):
        # Basic validation
        qty = data.get("quantity", 1) or 1
        if int(qty) < 1:
            raise serializers.ValidationError({"quantity": "Quantity must be at least 1"})
        deposit = data.get("deposit_amount", 0) or 0
        try:
            if Decimal(str(deposit)) < 0:
                raise serializers.ValidationError({"deposit_amount": "Deposit cannot be negative"})
        except Exception:
            raise serializers.ValidationError({"deposit_amount": "Invalid deposit amount"})
        return data

    def create(self, validated_data):
        """
        - If instant job: delegate to job_service.create_instant_job for atomic logic.
        - Else: snapshot unit_price and total, save, and attach to DaySheet idempotently.
        """
        request = self.context.get("request", None)
        user = request.user if request is not None and request.user.is_authenticated else None

        job_type = validated_data.get("type", None)
        if job_type == "instant":
            # delegate to service: returns Job instance
            job = job_service.create_instant_job(
                branch_id=validated_data["branch"].id,
                service_id=validated_data["service"].id,
                quantity=validated_data.get("quantity", 1),
                created_by=user,
                customer_name=validated_data.get("customer_name"),
                customer_phone=validated_data.get("customer_phone"),
                deposit=validated_data.get("deposit_amount", 0),
                description=validated_data.get("description", ""),
            )
            return job

        # Non-instant (queued) path: create snapshot and attach
        if "branch" not in validated_data or "service" not in validated_data:
            raise serializers.ValidationError("branch and service are required for queued jobs")

        with transaction.atomic():
            data = dict(validated_data)
            svc = validated_data.get("service")
            unit_price = getattr(svc, "price", None) or validated_data.get("price") or Decimal("0.00")
            try:
                unit_price = Decimal(str(unit_price))
            except Exception:
                unit_price = Decimal("0.00")
            data["unit_price"] = unit_price

            qty = int(validated_data.get("quantity", 1) or 1)
            deposit = validated_data.get("deposit_amount", 0) or 0
            try:
                total = (Decimal(unit_price) * qty) - Decimal(str(deposit or 0))
            except Exception:
                total = Decimal("0.00")
            if total < 0:
                total = Decimal("0.00")
            data["total_amount"] = total.quantize(Decimal("0.01"))

            # if caller passed created_by via perform_create, prefer that value
            created_by_override = validated_data.get("created_by") or self.initial_data.get("created_by")
            if created_by_override and not isinstance(created_by_override, type(user)):
                # ignore if not consistent; we'll instead prefer the request user below
                created_by_override = None

            if not data.get("created_by") and user:
                data["created_by"] = user

            instance = Job.objects.create(**data)

            # attach to daysheet (idempotent) - best-effort
            try:
                job_service.attach_job_to_daysheet_idempotent(instance, user=user, now=timezone.now())
            except Exception as exc:
                logger.debug("attach_job_to_daysheet_idempotent failed for job %s: %s", getattr(instance, "pk", None), exc)

            return instance
