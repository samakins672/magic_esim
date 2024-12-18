from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import eSIMPlan


class PlanListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plans = eSIMPlan.objects.all().values()
        return Response(plans)
