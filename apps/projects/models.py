from django.conf import settings
from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Customer(TimestampedModel):
    name = models.CharField(max_length=128)
    customer_code = models.CharField(max_length=64, unique=True)
    contact_name = models.CharField(max_length=64)
    contact_phone = models.CharField(max_length=32)
    service_level = models.CharField(max_length=32, blank=True)

    def __str__(self) -> str:
        return f"{self.customer_code}-{self.name}"


class Equipment(TimestampedModel):
    equipment_code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    category = models.CharField(max_length=64)
    model = models.CharField(max_length=64)
    running_status = models.CharField(max_length=32, default="normal")

    def __str__(self) -> str:
        return f"{self.equipment_code}-{self.name}"


class Engineer(TimestampedModel):
    class SkillLevel(models.TextChoices):
        JUNIOR = "junior", "初级"
        MIDDLE = "middle", "中级"
        SENIOR = "senior", "高级"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    region = models.CharField(max_length=64)
    skill_level = models.CharField(max_length=16, choices=SkillLevel.choices)
    skills = models.JSONField(default=list)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.user.get_full_name() or self.user.username


class SparePart(TimestampedModel):
    part_code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    model = models.CharField(max_length=64)
    stock_quantity = models.PositiveIntegerField(default=0)
    safety_stock = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.CharField(max_length=128)

    @property
    def low_stock(self) -> bool:
        return self.stock_quantity < self.safety_stock


class Project(TimestampedModel):
    class ProjectType(models.TextChoices):
        REPAIR = "repair", "故障维修"
        MAINTENANCE = "maintenance", "定期维保"
        INSPECTION = "inspection", "巡检改造"
        EMERGENCY = "emergency", "应急抢修"
        RETURN_FACTORY = "return_factory", "寄修返厂"

    class Priority(models.TextChoices):
        LOW = "low", "低"
        MIDDLE = "middle", "中"
        HIGH = "high", "高"
        URGENT = "urgent", "紧急"

    class Status(models.TextChoices):
        RECEIVED = "received", "已受理"
        REVIEWING = "reviewing", "审核中"
        DISPATCHED = "dispatched", "已派工"
        EXECUTING = "executing", "执行中"
        TO_ACCEPT = "to_accept", "待验收"
        TO_SETTLE = "to_settle", "待结算"
        CLOSED = "closed", "已归档"

    project_no = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=128)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT)
    project_type = models.CharField(max_length=32, choices=ProjectType.choices)
    priority = models.CharField(max_length=16, choices=Priority.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RECEIVED)
    amount_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    issue_description = models.TextField()
    planned_start = models.DateField(null=True, blank=True)
    planned_end = models.DateField(null=True, blank=True)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_projects")

    def __str__(self) -> str:
        return self.project_no


class ApprovalRecord(TimestampedModel):
    class Node(models.TextChoices):
        SUPERVISOR = "supervisor", "服务主管"
        TECH_LEAD = "tech_lead", "技术负责人"
        FINANCE = "finance", "财务负责人"
        GM = "gm", "总经理"

    class Decision(models.TextChoices):
        PENDING = "pending", "待审批"
        APPROVED = "approved", "通过"
        REJECTED = "rejected", "驳回"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="approvals")
    node = models.CharField(max_length=16, choices=Node.choices)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    decision = models.CharField(max_length=16, choices=Decision.choices, default=Decision.PENDING)
    comment = models.TextField(blank=True)


class DispatchOrder(TimestampedModel):
    class DispatchMode(models.TextChoices):
        MANUAL = "manual", "手动派工"
        AUTO = "auto", "自动派工"
        MAP = "map", "地图派工"
        GRAB = "grab", "抢单"

    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="dispatch")
    engineer = models.ForeignKey(Engineer, on_delete=models.PROTECT)
    mode = models.CharField(max_length=16, choices=DispatchMode.choices)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    assigned_at = models.DateTimeField(auto_now_add=True)


class ExecutionRecord(TimestampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="execution_records")
    engineer = models.ForeignKey(Engineer, on_delete=models.PROTECT)
    sign_in_time = models.DateTimeField(null=True, blank=True)
    sign_in_latitude = models.FloatField(null=True, blank=True)
    sign_in_longitude = models.FloatField(null=True, blank=True)
    work_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    work_detail = models.TextField()
    report_url = models.URLField(blank=True)


class PartUsage(TimestampedModel):
    execution_record = models.ForeignKey(ExecutionRecord, on_delete=models.CASCADE, related_name="part_usages")
    spare_part = models.ForeignKey(SparePart, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()


class Settlement(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "待审核"
        MANAGER_APPROVED = "manager_approved", "经理通过"
        FINANCE_APPROVED = "finance_approved", "财务通过"

    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="settlement")
    labor_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    part_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    travel_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT)
