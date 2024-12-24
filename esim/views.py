import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .serializers import eSIMPlanFilterSerializer, eSIMProfileSerializer
from decouple import config

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
                    return Response({
                        "status": True,
                        "message": "eSIM profile fetched successfully.",
                        "data": response.json().get('obj', {})  # Extract 'obj' object from the API response
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