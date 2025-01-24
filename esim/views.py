import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from magic_esim.permissions import IsAuthenticatedWithSessionOrJWT
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import eSIMPlan
from .serializers import eSIMPlanFilterSerializer, eSIMProfileSerializer, eSIMPlanSerializer
from decouple import config
import json
import os
from django.conf import settings


class eSIMPlanListView(APIView):
    """
    View to fetch eSIM plans from the external API and filter based on supported fields.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter("locationCode", OpenApiTypes.STR, description="Location code (e.g., US, IN)", required=False),
            OpenApiParameter("type", OpenApiTypes.STR, description="Type of plan (e.g., data, voice)", required=False),
            OpenApiParameter("slug", OpenApiTypes.STR, description="Slug identifier for the plan", required=False),
            OpenApiParameter("packageCode", OpenApiTypes.STR, description="Package code of the plan", required=False),
            OpenApiParameter("iccid", OpenApiTypes.STR, description="ICCID for the eSIM", required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        serializer = eSIMPlanFilterSerializer(data=request.query_params)
        if serializer.is_valid():
            # Extract validated fields
            filters = serializer.validated_data
            
            try:
                esim_host = config('ESIMACCESS_HOST')
                api_token = config('ESIMACCESS_ACCESS_CODE')

                response = requests.post(
                    f"{esim_host}/api/v1/open/package/list",
                    json=filters,
                    headers={"RT-AccessCode": api_token},
                )
                if response.status_code == 200:
                    # Return the data from the external API
                    return Response({
                        "status": True,
                        "message": "eSIM plans fetched successfully.",
                        "data": response.json().get('obj', [])  # Extract 'obj' array from the API response
                    }, status=status.HTTP_200_OK)
                else:
                    # Handle non-200 responses from the external API
                    return Response({
                        "status": False,
                        "message": "Failed to fetch eSIM plans.",
                        "error": response.json(),
                    }, status=response.status_code)
            except requests.RequestException as e:
                # Handle exceptions during the request
                return Response({
                    "status": False,
                    "message": "Error connecting to the eSIM API.",
                    "error": str(e),
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Validation failed
            return Response({
                "status": False,
                "message": "Invalid input parameters.",
                "errors": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)


class eSIMProfileView(APIView):
    """
    View to fetch eSIM profile details based on the orderNo or ICCID.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter("orderNo", OpenApiTypes.STR, description="Order number for the eSIM profile e.g. B2210206381924", required=False),
            OpenApiParameter("iccid", OpenApiTypes.STR, description="ICCID for the eSIM", required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        serializer = eSIMProfileSerializer(data=request.query_params)
        if serializer.is_valid():
            # Extract validated fields
            filters = serializer.validated_data
            
            try:
                esim_host = config('ESIMACCESS_HOST')
                api_token = config('ESIMACCESS_ACCESS_CODE')

                response = requests.post(
                    f"{esim_host}/api/v1/open/esim/query",
                    json=filters,
                    headers={"RT-AccessCode": api_token},
                )
                if response.status_code == 200 and response.json().get('success', False):
                    # Return the data from the external API
                    data = response.json().get('obj', {}).get('esimList', [])

                    # Enrich data with time_created from the database
                    enriched_data = []
                    for item in data:
                        order_no = item.get('orderNo')  # Extract order number
                        if order_no:
                            try:
                                esim_plan = eSIMPlan.objects.get(order_no=order_no)
                                item['price'] = esim_plan.price
                            except eSIMPlan.DoesNotExist:
                                item['price'] = None
                        enriched_data.append(item)

                    print(enriched_data)
                    return Response({
                        "status": True,
                        "message": "eSIM profile fetched successfully.",
                        "data": data
                    }, status=status.HTTP_200_OK)
                else:
                    # Handle non-200 responses or status is not True from the external API
                    return Response({
                        "status": False,
                        "message": "Failed to fetch eSIM profile.",
                        "error": response.json().get('errorMsg', {}),
                    }, status=response.status_code)
            except requests.RequestException as e:
                # Handle exceptions during the request
                return Response({
                    "status": False,
                    "message": "Error connecting to the eSIM API.",
                    "error": str(e),
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Validation failed
            return Response({
                "status": False,
                "message": "Invalid input parameters.",
                "errors": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        

class eSIMPlanListCreateView(generics.ListCreateAPIView):
    """
    Handles listing all eSIM plans and creating a new eSIM plan.
    """
    serializer_class = eSIMPlanSerializer
    permission_classes = [IsAuthenticatedWithSessionOrJWT]

    def get_queryset(self):
        # Return only the eSIM plans associated with the authenticated user
        user = self.request.user
        plans = eSIMPlan.objects.filter(user=user)
        
        # Update volume_used field for each plan
        for plan in plans:
            try:
                esim_host = config('ESIMACCESS_HOST')
                api_token = config('ESIMACCESS_ACCESS_CODE')
                params = {
                    "orderNo": plan.order_no,
                    "iccid": "",
                    "pager":{
                        "pageNum":1,
                        "pageSize":20
                    }
                }

                response = requests.post(
                    f"{esim_host}/api/v1/open/esim/query",
                    json=params,
                    headers={"RT-AccessCode": api_token},
                )
                if response.status_code == 200 and response.json().get('success', False):
                    profile_data = response.json().get('obj', {})
                    profile_data = profile_data.get('esimList', {})[0]
                # Log the profile data
                print(f"Profile data: {profile_data}")
                plan.activated_on = profile_data.get('activateTime', plan.activated_on)
                plan.volume_used = profile_data.get('orderUsage', plan.volume_used)
                plan.save()
            except requests.RequestException as e:
                # Log the error
                print(f"Error fetching eSIM profile: {e}")
        
        return plans


class eSIMPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, and deleting a specific eSIM plan.
    """
    serializer_class = eSIMPlanSerializer
    permission_classes = [IsAuthenticatedWithSessionOrJWT]

    def get_queryset(self):
        # Return only the eSIM plans associated with the authenticated user
        return eSIMPlan.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "status": True,
            "message": "eSIM plan updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class CountriesListView(APIView):
    """
    View to fetch list of countries from JSON file.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Get list of all countries"
    )
    def get(self, request):
        try:
            json_file_path = os.path.join(settings.BASE_DIR, 'static', 'vendor', 'locations', 'countries.json')
            with open(json_file_path, 'r') as file:
                countries = json.load(file)
            
            return Response({
                "status": True,
                "message": "Countries list fetched successfully.",
                "data": countries
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "message": "Failed to fetch countries list.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PopularCountriesListView(APIView):
    """
    View to fetch list of popular countries from JSON file.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Get list of popular countries"
    )
    def get(self, request):
        try:
            json_file_path = os.path.join(settings.BASE_DIR, 'static', 'vendor', 'locations', 'popular_countries.json')
            with open(json_file_path, 'r') as file:
                countries = json.load(file)
            
            return Response({
                "status": True,
                "message": "Popular countries list fetched successfully.",
                "data": countries
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "message": "Failed to fetch popular countries list.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)