from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.utils.timezone import now
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ApprovalRecord, DispatchOrder, Engineer, Project
from .serializers import (
    ApprovalRecordSerializer,
    DispatchOrderSerializer,
    ExecutionRecordSerializer,
    ProjectSerializer,
    SettlementCreateSerializer,
    SettlementSerializer,
)
from .services import approval_nodes_by_amount, choose_engineer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.select_related("customer", "equipment", "requester")
    serializer_class = ProjectSerializer

    def perform_create(self, serializer):
        ts = now()
        project_type = serializer.validated_data["project_type"][:3].upper()
        serial = Project.objects.filter(created_at__date=ts.date()).count() + 1
        project_no = f"{ts:%Y%m}{project_type}{serial:04d}"
        serializer.save(project_no=project_no, status=Project.Status.REVIEWING)

    @action(detail=True, methods=["post"])
    def submit_for_approval(self, request, pk=None):
        project = self.get_object()
        reviewer_map = request.data.get("reviewer_map", {})
        nodes = approval_nodes_by_amount(project.amount_estimate)

        created = []
        for node in nodes:
            reviewer_id = reviewer_map.get(node)
            if not reviewer_id:
                return Response({"detail": f"节点 {node} 缺少审核人"}, status=status.HTTP_400_BAD_REQUEST)
            created.append(
                ApprovalRecord(
                    project=project,
                    node=node,
                    reviewer_id=reviewer_id,
                    comment="系统生成审批任务",
                )
            )

        with transaction.atomic():
            ApprovalRecord.objects.filter(project=project).delete()
            ApprovalRecord.objects.bulk_create(created)
            project.status = Project.Status.REVIEWING
            project.save(update_fields=["status", "updated_at"])

        return Response(ApprovalRecordSerializer(created, many=True).data)

    @action(detail=True, methods=["post"])
    def auto_dispatch(self, request, pk=None):
        project = self.get_object()
        site_lat = float(request.data["site_lat"])
        site_lng = float(request.data["site_lng"])

        engineers = Engineer.objects.filter(region=request.data.get("region", ""))
        candidate = choose_engineer(project, engineers, site_lat=site_lat, site_lng=site_lng)
        if candidate is None:
            return Response({"detail": "无可用工程师"}, status=status.HTTP_400_BAD_REQUEST)

        dispatch, _ = DispatchOrder.objects.update_or_create(
            project=project,
            defaults={
                "engineer": candidate.engineer,
                "mode": DispatchOrder.DispatchMode.AUTO,
                "assigned_by": request.user,
            },
        )
        project.status = Project.Status.DISPATCHED
        project.save(update_fields=["status", "updated_at"])

        return Response(DispatchOrderSerializer(dispatch).data)

    @action(detail=True, methods=["post"])
    def create_settlement(self, request, pk=None):
        project = self.get_object()
        serializer = SettlementCreateSerializer(data=request.data, context={"project": project})
        serializer.is_valid(raise_exception=True)
        settlement = serializer.save()
        project.status = Project.Status.TO_SETTLE
        project.save(update_fields=["status", "updated_at"])
        return Response(SettlementSerializer(settlement).data)


class ApprovalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ApprovalRecord.objects.select_related("project", "reviewer")
    serializer_class = ApprovalRecordSerializer

    @action(detail=True, methods=["post"])
    def decide(self, request, pk=None):
        approval = self.get_object()
        decision = request.data.get("decision")
        comment = request.data.get("comment", "")
        if decision not in [ApprovalRecord.Decision.APPROVED, ApprovalRecord.Decision.REJECTED]:
            return Response({"detail": "非法的审批结果"}, status=status.HTTP_400_BAD_REQUEST)

        approval.decision = decision
        approval.comment = comment
        approval.save(update_fields=["decision", "comment", "updated_at"])

        project = approval.project
        decisions = project.approvals.values_list("decision", flat=True)
        if ApprovalRecord.Decision.REJECTED in decisions:
            project.status = Project.Status.RECEIVED
        elif all(item == ApprovalRecord.Decision.APPROVED for item in decisions):
            project.status = Project.Status.DISPATCHED
        project.save(update_fields=["status", "updated_at"])

        return Response(ApprovalRecordSerializer(approval).data)
