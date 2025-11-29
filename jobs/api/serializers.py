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
    class Meta:
        model = Job
        fields = [
            "id","branch","service","customer_name","customer_phone","description",
            "quantity","price","unit_price","total_amount","deposit_amount",
            "expected_minutes_per_unit","priority","type","status",
            "queue_position","expected_ready_at","completed_at","created_by","created_at",
        ]
        read_only_fields = ["id","unit_price","total_amount","queue_position","expected_ready_at","completed_at","created_at","created_by","status"]

    def create(self, validated_data):
        # don't create instant job here — use jobs_services.create_instant_job for atomic logic
        request = self.context.get("request")
        if validated_data.get("type") == "instant":
            # delegate to service to ensure snapshot + daily sale update
            from jobs.jobs_services import create_instant_job
            job = create_instant_job(
                branch_id=validated_data["branch"].id,
                service_id=validated_data["service"].id,
                quantity=validated_data.get("quantity",1),
                created_by=request.user if request else None,
                customer_name=validated_data.get("customer_name"),
                customer_phone=validated_data.get("customer_phone"),
                deposit=validated_data.get("deposit_amount", 0),
                description=validated_data.get("description",""),
            )
            return job
        return super().create(validated_data)
