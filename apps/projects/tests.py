from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Customer, Engineer, Equipment, ExecutionRecord, PartUsage, Project, SparePart
from .services import approval_nodes_by_amount, calculate_settlement


class ProjectServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="test123456")
        self.customer = Customer.objects.create(
            name="测试客户",
            customer_code="C001",
            contact_name="张三",
            contact_phone="13800000000",
        )
        self.equipment = Equipment.objects.create(
            equipment_code="E001",
            name="道岔融雪设备",
            category="融雪",
            model="RS-100",
        )

    def test_approval_nodes_by_amount(self):
        self.assertEqual(len(approval_nodes_by_amount(Decimal("5000"))), 1)
        self.assertEqual(len(approval_nodes_by_amount(Decimal("30000"))), 2)
        self.assertEqual(len(approval_nodes_by_amount(Decimal("80000"))), 4)

    def test_calculate_settlement(self):
        project = Project.objects.create(
            project_no="202501REP0001",
            name="测试维修",
            customer=self.customer,
            equipment=self.equipment,
            project_type=Project.ProjectType.REPAIR,
            priority=Project.Priority.HIGH,
            amount_estimate=Decimal("12000"),
            issue_description="故障",
            requester=self.user,
        )

        engineer = Engineer.objects.create(
            user=self.user,
            region="北京",
            skill_level=Engineer.SkillLevel.SENIOR,
            skills=[Project.ProjectType.REPAIR],
        )
        record = ExecutionRecord.objects.create(project=project, engineer=engineer, work_detail="处理完成", work_hours=Decimal("3"))
        part = SparePart.objects.create(
            part_code="P001",
            name="电源模块",
            model="M1",
            stock_quantity=10,
            safety_stock=2,
            unit_cost=Decimal("100"),
            supplier="供应商A",
        )
        PartUsage.objects.create(execution_record=record, spare_part=part, quantity=2)

        result = calculate_settlement(project, labor_hour_rate=Decimal("200"), travel_cost=Decimal("50"), other_cost=Decimal("10"))
        self.assertEqual(result["labor_cost"], Decimal("600.00"))
        self.assertEqual(result["part_cost"], Decimal("210.00"))
        self.assertEqual(result["total_amount"], Decimal("870.00"))
