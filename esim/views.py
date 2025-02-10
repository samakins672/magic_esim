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
    View to fetch eSIM plans from:
      - esimaccess (POST request, existing logic)
      - esimgo (GET request, new logic)
    based on a 'platform' query parameter.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            # Existing filters from your eSIMPlanFilterSerializer
            OpenApiParameter("locationCode", OpenApiTypes.STR, description="Location code (e.g., US, IN)", required=False),
            OpenApiParameter("type", OpenApiTypes.STR, description="Type of plan (e.g., data, voice)", required=False),
            OpenApiParameter("slug", OpenApiTypes.STR, description="Slug identifier for the plan", required=False),
            OpenApiParameter("packageCode", OpenApiTypes.STR, description="Package code of the plan", required=False),
            OpenApiParameter("iccid", OpenApiTypes.STR, description="ICCID for the eSIM", required=False),
            OpenApiParameter("mainRegion", OpenApiTypes.STR, description="main Region codes", required=False),

            # Which API to call
            OpenApiParameter("platform", OpenApiTypes.STR, description="Which platform to call: esimaccess or esimgo", required=False),

            # eSIM-Go specific params (some might be used only locally for filtering):
            # OpenApiParameter("group", OpenApiTypes.STR, description="Group(s) for eSIM-Go (e.g. 'Standard+Unlimited+Essential')", required=False),
            OpenApiParameter("countries", OpenApiTypes.STR, description="Countries for eSIM-Go (e.g. 'NG')", required=False),
            OpenApiParameter("region", OpenApiTypes.STR, description="Region for local filtering (e.g. 'Africa')", required=False),
            OpenApiParameter("description", OpenApiTypes.STR, description="Description substring filter for local filtering", required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        """
        Depending on 'platform', call either eSIMAccess or eSIM-Go API.
        """
        serializer = eSIMPlanFilterSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                {
                    "status": False,
                    "message": "Invalid input parameters.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract validated fields (from your serializer)
        filters = serializer.validated_data

        # Determine platform
        platform = request.query_params.get("platform", "esimaccess").lower()

        try:
            # ---------------------------------------------------------------
            # 1) eSIM-Go Logic (GET)
            # ---------------------------------------------------------------
            if platform == "esimgo":
                # Pull from env (or hardcode if it's always the same)
                esimgo_host = config("ESIMGO_HOST")
                esimgo_api_key = config("ESIMGO_API_KEY")

                # eSIM-Go frequently filters by 'countries' and 'group' in the query params
                group_param = "Standard Unlimited Essential"
                countries_param = request.query_params.get("countries", "")
                region_param = request.query_params.get("region", "")        # e.g. "Africa"
                desc_param = request.query_params.get("description", "")     # e.g. substring to match in bundle description

                # Build the GET URL
                url = (
                    f"{esimgo_host}/catalogue?"
                    f"group={group_param}&countries={countries_param}&region={region_param}&description={desc_param}"
                    f"&api_key={esimgo_api_key}"
                )

                # Prepare headers
                headers = {
                    "accept": "application/json",
                    "x-api-key": esimgo_api_key
                }

                # Make request
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    return Response(
                        {
                            "status": False,
                            "message": "Failed to fetch eSIM plans from eSIM-Go.",
                            "error": response.text,
                        },
                        status=response.status_code
                    )

                # Parse the response
                data = response.json().get("bundles", [])

                # Further local filtering based on region and description
                if region_param:
                    # Keep only bundles that have at least one country with region containing region_param
                    data = [
                        bundle for bundle in data
                        if any(
                            region_param in country.get("iso", "")
                            for country in bundle.get("countries", [])
                        )
                    ]

                # Example transformation: adding formattedVolume / formattedPrice
                for item in data:
                    # Volume
                    if item.get("unlimited") or item.get("dataAmount", -1) < 0:
                        item["formattedVolume"] = "Unlimited"
                    else:
                        # eSIM-Go dataAmount is in MB
                        data_mb = item["dataAmount"]
                        if data_mb >= 1024:
                            item["formattedVolume"] = f"{(data_mb / 1024):.1f} GB"
                        else:
                            item["formattedVolume"] = f"{data_mb} MB"

                    # Price
                    price = item.get("price", 0)
                    item["formattedPrice"] = f"{(price * 2):.2f}"

                return Response(
                    {
                        "status": True,
                        "message": "eSIM plans fetched successfully from eSIM-Go.",
                        "data": data
                    },
                    status=status.HTTP_200_OK
                )

            # ---------------------------------------------------------------
            # 2) eSIMAccess Logic (POST, existing)
            # ---------------------------------------------------------------
            else:
                esim_host = config("ESIMACCESS_HOST")
                api_token = config("ESIMACCESS_ACCESS_CODE")

                response = requests.post(
                    f"{esim_host}/api/v1/open/package/list",
                    json=filters,
                    headers={"RT-AccessCode": api_token},
                )

                if response.status_code == 200:
                    data = response.json().get('obj', {})
                    # Check if mainRegion was passed and filter the data accordingly
                    main_region = filters.get('mainRegion')
                    if main_region:
                        data = data.get('packageList', [])
                        data = [item for item in data if item.get('slug', '').startswith(main_region)]

                        # Sort by price ascending
                        data = sorted(data, key=lambda x: x.get('price', float('inf')))

                        # Convert volume from bytes to GB/MB
                        for item in data:
                            volume_bytes = item.get('volume', 0)
                            if volume_bytes >= 1024 ** 3:
                                item['formattedVolume'] = f"{(volume_bytes / (1024 ** 3)):.1f} GB"
                            else:
                                item['formattedVolume'] = f"{(volume_bytes / (1024 ** 2)):.0f} MB"

                            # Format the price
                            price = item.get('price', 0)
                            item['formattedPrice'] = f"{((price / 10000) * 2):.2f}"

                    return Response(
                        {
                            "status": True,
                            "message": "eSIM plans fetched successfully from eSIMAccess.",
                            "data": data
                        },
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {
                            "status": False,
                            "message": "Failed to fetch eSIM plans from eSIMAccess.",
                            "error": response.json(),
                        },
                        status=response.status_code
                    )

        except requests.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"Error connecting to {platform} eSIM API.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        return eSIMPlan.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        user = self.request.user
        plans = self.get_queryset()

        # Update volume_used field for each plan
        updated_plans = []
        for plan in plans:
            try:
                esim_host = config("ESIMACCESS_HOST")
                api_token = config("ESIMACCESS_ACCESS_CODE")
                params = {
                    "orderNo": plan.order_no,
                    "iccid": "",
                    "pager": {
                        "pageNum": 1,
                        "pageSize": 20
                    }
                }

                response = requests.post(
                    f"{esim_host}/api/v1/open/esim/query",
                    json=params,
                    headers={"RT-AccessCode": api_token},
                )

                if response.status_code == 200:
                    api_response = response.json()
                    if api_response.get("success", False):
                        profile_data = api_response.get("obj", {}).get("esimList", [])
                        if profile_data:
                            esim = profile_data[0]
                            # Update plan details
                            plan.activated_on = esim.get("activateTime", plan.activated_on)
                            plan.volume_used = esim.get("orderUsage", plan.volume_used)
                            plan.save()
                        else:
                            print(f"No eSIM data found for plan {plan.order_no}.")
                    else:
                        print(f"API error for plan {plan.order_no}: {api_response.get('errorMsg', 'Unknown error')}")
                else:
                    print(f"HTTP error {response.status_code} for plan {plan.order_no}: {response.text}")
            except requests.RequestException as e:
                print(f"Error fetching eSIM profile for plan {plan.order_no}: {e}")

            updated_plans.append(plan)

        # Serialize the updated plans
        serializer = self.get_serializer(updated_plans, many=True)
        return Response({
            "status": True,
            "message": "User eSIM plans fetched successfully.",
            "data": serializer.data,
        }, status=status.HTTP_200_OK)


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
            
            # Convert alpha_2 to lowercase
            for country in countries:
                country['alpha_2_lower'] = country['alpha_2'].lower()
            
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
            
            # Convert alpha_2 to lowercase
            for country in countries:
                country['alpha_2_lower'] = country['alpha_2'].lower()
            
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