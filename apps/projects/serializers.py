from rest_framework import serializers

from .models import ApprovalRecord, DispatchOrder, ExecutionRecord, Project, Settlement
from .services import calculate_settlement


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = ("project_no", "status")


class ApprovalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRecord
        fields = "__all__"


class DispatchOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispatchOrder
        fields = "__all__"


class ExecutionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutionRecord
        fields = "__all__"


class SettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settlement
        fields = "__all__"
        read_only_fields = ("labor_cost", "part_cost", "total_amount", "status")


class SettlementCreateSerializer(serializers.Serializer):
    labor_hour_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    travel_cost = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_cost = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)

    def create(self, validated_data):
        project = self.context["project"]
        costs = calculate_settlement(project=project, **validated_data)
        settlement, _ = Settlement.objects.update_or_create(project=project, defaults=costs)
        return settlement
