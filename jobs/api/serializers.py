from rest_framework import serializers
from jobs.models import Job, JobRecord, JobAttachment
from django.contrib.auth import get_user_model

User = get_user_model()


class JobAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = JobAttachment
        fields = ["id", "file", "note", "uploaded_by", "created_at"]


class JobRecordSerializer(serializers.ModelSerializer):
    attachments = JobAttachmentSerializer(many=True, read_only=True)
    performed_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)

    class Meta:
        model = JobRecord
        fields = [
            "id", "job", "performed_by", "time_start", "time_end",
            "quantity_produced", "notes", "issues", "attachments", "created_at"
        ]


class JobSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    queue_position = serializers.IntegerField(read_only=True)
    expected_ready_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Job
        fields = [
            "id", "branch", "service", "customer_name", "customer_phone",
            "description", "quantity", "price", "deposit_amount",
            "expected_minutes_per_unit", "priority", "status",
            "queue_position", "expected_ready_at", "created_by", "created_at"
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault("created_by", request.user)
        job = super().create(validated_data)
        # compute queue position and ETA
        from .helpers import compute_queue_position_and_eta
        queue_pos, eta = compute_queue_position_and_eta(job)
        job.queue_position = queue_pos
        job.expected_ready_at = eta
        job.save(update_fields=["queue_position", "expected_ready_at"])
        return job
