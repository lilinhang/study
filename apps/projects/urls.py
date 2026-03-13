from rest_framework.routers import DefaultRouter

from .views import ApprovalViewSet, ProjectViewSet

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="project")
router.register("approvals", ApprovalViewSet, basename="approval")

urlpatterns = router.urls
