from django.contrib import admin

from .models import (
    ApprovalRecord,
    Customer,
    DispatchOrder,
    Engineer,
    Equipment,
    ExecutionRecord,
    PartUsage,
    Project,
    Settlement,
    SparePart,
)

admin.site.register(Customer)
admin.site.register(Equipment)
admin.site.register(Engineer)
admin.site.register(SparePart)
admin.site.register(Project)
admin.site.register(ApprovalRecord)
admin.site.register(DispatchOrder)
admin.site.register(ExecutionRecord)
admin.site.register(PartUsage)
admin.site.register(Settlement)
