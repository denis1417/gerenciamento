from rest_framework.routers import DefaultRouter
from .api_views import ProdutoViewSet, InsumoViewSet, ColaboradorViewSet

router = DefaultRouter()

router.register(r'produtos', ProdutoViewSet)
router.register(r'insumos', InsumoViewSet)
router.register(r'colaboradores', ColaboradorViewSet)

urlpatterns = router.urls
