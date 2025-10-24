import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from magic_esim.permissions import IsAuthenticatedWithSessionOrJWT
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from .models import eSIMPlan
from .serializers import (
    CountryListResponseSerializer,
    ESIMGoPlanDetailResponseSerializer,
    eSIMBaseResponseSerializer,
    eSIMPlanFilterSerializer,
    eSIMPlanListResponseSerializer,
    eSIMPlanSerializer,
    eSIMProfileResponseSerializer,
    eSIMProfileSerializer,
    eSIMUserPlanListResponseSerializer,
    eSIMUserPlanResponseSerializer,
)
from decouple import config
import json
import os
from django.conf import settings
from datetime import datetime, timedelta


class eSIMPlanListView(APIView):
    """
    View to fetch plans from both:
      - eSIMAccess (POST request)
      - eSIMGo (GET request)

    Results are combined in a single response under:
      data: {
         "standard": [... eSIMAccess results ...],
         "unlimited": [... eSIMGo results ...]
      }
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["eSIM"],
        summary="List available eSIM plans",
        description="Fetch catalogue data from eSIMAccess and eSIMGo and merge the results into grouped collections.",
        parameters=[
            # Existing filters from your eSIMPlanFilterSerializer
            OpenApiParameter("locationCode", OpenApiTypes.STR, description="Location code (e.g., US, IN)", required=False),
            OpenApiParameter("type", OpenApiTypes.STR, description="Type of plan (e.g., data, voice)", required=False),
            OpenApiParameter("slug", OpenApiTypes.STR, description="Slug identifier for the plan", required=False),
            OpenApiParameter("packageCode", OpenApiTypes.STR, description="Package code of the plan", required=False),
            OpenApiParameter("iccid", OpenApiTypes.STR, description="ICCID for the eSIM", required=False),
            OpenApiParameter("mainRegion", OpenApiTypes.STR, description="Main region filter for global catalogues", required=False),

            # eSIM-Go additional filters
            OpenApiParameter("region", OpenApiTypes.STR, description="Region for local filtering (e.g. 'Africa')", required=False),
            OpenApiParameter("description", OpenApiTypes.STR, description="Description substring filter for local filtering", required=False),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=eSIMPlanListResponseSerializer,
                description="Combined catalogue data retrieved successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="Invalid filter parameters supplied.",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Fetch and combine results from both eSIMAccess and eSIMGo.
        - eSIMAccess results stored in standard[]
        - eSIMGo results stored in unlimited[]
        """
        # Validate query params against your serializer
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
        filters = serializer.validated_data

        package_code = filters.get("packageCode")
        if isinstance(package_code, str):
            normalized_package_code = package_code.strip()
            if not normalized_package_code:
                filters.pop("packageCode", None)
            elif normalized_package_code.lower() in {"null", "undefined"}:
                return Response(
                    {
                        "status": False,
                        "message": "A valid packageCode must be provided to retrieve plan details.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                filters["packageCode"] = normalized_package_code
        elif package_code is None:
            filters.pop("packageCode", None)

        # Prepare empty lists for each
        standard_data = []   # Will hold eSIMAccess results
        unlimited_data = []  # Will hold eSIMGo results

        # =========================================================
        # 1) Fetch from eSIMAccess (STANDARD)
        # =========================================================
        try:
            esim_host = config("ESIMACCESS_HOST")
            api_token = config("ESIMACCESS_ACCESS_CODE")

            response = requests.post(
                f"{esim_host}/api/v1/open/package/list",
                json=filters,  # includes e.g. locationCode, type, etc.
                headers={"RT-AccessCode": api_token},
                timeout=15
            )

            if response.status_code == 200:
                access_obj = response.json().get("obj") or {}
                packages = access_obj.get("packageList", [])

                # Filter packages where slug starts with locationCode and doesn't end with _END or _DAILY
                location_code = filters.get("locationCode")
                if location_code and location_code != '!RG' and location_code != '!GL':
                    packages = [
                        item for item in packages
                        if item.get("slug", "").startswith(f"{location_code}_") and not item.get("slug", "").endswith(("_End", "_Daily"))
                    ]

                # If mainRegion was passed, filter
                main_region = filters.get("mainRegion")
                if main_region and location_code == '!RG':
                    packages = [
                        item for item in packages
                        if item.get("slug", "").startswith(f"{main_region}-") and not item.get("slug", "").endswith(("_End", "_Daily"))
                    ]
                    
                elif main_region and location_code == '!GL':
                    packages = [
                        item for item in packages
                        if item.get("slug", "").startswith(main_region) and not item.get("slug", "").endswith(("_End", "_Daily"))
                    ]


                # Sort by price ascending
                packages = sorted(packages, key=lambda x: x.get("price", float("inf")))

                # Convert volume from bytes to GB/MB and format prices
                for item in packages:
                    volume_bytes = item.get("volume", 0)

                    if volume_bytes >= 1024 ** 3:
                        item["formattedVolume"] = f"{(volume_bytes / (1024 ** 3)):.1f} GB"
                    else:
                        item["formattedVolume"] = f"{(volume_bytes / (1024 ** 2)):.0f} MB"

                    # Price format (existing logic: (price / 10000) * 2)
                    price = item.get("price", 0)
                    item["formattedPrice"] = f"{((price / 10000) * 2):.2f}"

                standard_data = packages

            else:
                # If non-200, you could log or return a partial success
                # We'll simply store an empty list (and optionally store the error in an attribute)
                print("Error fetching eSIMAccess data:", response.text)

        except requests.RequestException as e:
            print("Exception fetching eSIMAccess data:", e)
            # If you prefer, just let standard_data remain empty

        # =========================================================
        # 2) Fetch from eSIMGo (UNLIMITED)
        # =========================================================
        try:
            esimgo_host = config("ESIMGO_HOST")
            esimgo_api_key = config("ESIMGO_API_KEY")

            # eSIM-Go typically uses a GET request with 'countries' and 'group' in the query params.
            # We'll define the group as "Standard+Unlimited+Essential" or something similar
            # (You can adapt to your own logic as needed)
            group_param = "Standard Unlimited Essential"
            countries_param = request.query_params.get("locationCode", "")
            if '!' in countries_param:
                countries_param = ""
            region_param = request.query_params.get("region", "")
            desc_param = request.query_params.get("description", "")

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

            get_response = requests.get(url, headers=headers, timeout=15)

            if get_response.status_code == 200:
                bundles = get_response.json().get("bundles", [])

                # Local filtering
                if region_param:
                    # Keep only bundles that have at least one country with region or iso containing region_param
                    # Adjust logic as you prefer; the snippet below checks region in .iso or .region
                    bundles = [
                        bundle for bundle in bundles
                        if any(
                            region_param in country.get("iso", "")
                            for country in bundle.get("countries", [])
                        )
                    ]

                # Example transformation: adding formattedVolume / formattedPrice
                for item in bundles:
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

                    # Price: you used `(price * 2)` in your prior logic, adapt as needed
                    price = item.get("price", 0)
                    item["formattedPrice"] = f"{(price * 2):.2f}"

                unlimited_data = bundles

            else:
                print("Error fetching eSIMGo data:", get_response.text)

        except requests.RequestException as e:
            print("Exception fetching eSIMGo data:", e)
            # If you prefer, unlimited_data stays empty

        # =========================================================
        # 3) Combine both sets of data and return
        # =========================================================
        return Response(
            {
                "status": True,
                "message": "Fetched eSIM plans from both eSIMAccess and eSIMGo.",
                "data": {
                    "standard": standard_data,     # eSIMAccess
                    "unlimited": unlimited_data    # eSIMGo
                },
            },
            status=status.HTTP_200_OK
        )


class ESIMGoPlanDetailView(APIView):
    """
    Fetch a single eSIM-Go plan detail by 'name'.
    Example usage:
      GET /api/esimgo/plan-detail?name=esim_ULE_1D_CN_V2
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["eSIM"],
        summary="Retrieve a single eSIMGo bundle",
        parameters=[
            OpenApiParameter(
                name="name",
                type=OpenApiTypes.STR,
                description="The 'name' (e.g., 'esim_ULE_1D_CN_V2') of the eSIM-Go plan to fetch.",
                required=True
            ),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=ESIMGoPlanDetailResponseSerializer,
                description="Plan detail retrieved successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="The required plan name was not supplied.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="No plan exists for the supplied name.",
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="Unexpected error when contacting the eSIM-Go API.",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        """Retrieve a single eSIM-Go plan by 'name'."""
        # 1) Grab the 'name' from query parameters
        plan_name = request.query_params.get("name")
        if not plan_name:
            return Response(
                {
                    "status": False,
                    "message": "Missing required 'name' parameter for eSIM-Go plan."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2) Prepare eSIM-Go environment variables and the API URL
        esimgo_host = config("ESIMGO_HOST")
        esimgo_api_key = config("ESIMGO_API_KEY")

        url = f"{esimgo_host}/catalogue/bundle/{plan_name}?api_key={esimgo_api_key}"
        headers = {
            "accept": "application/json",
            "x-api-key": esimgo_api_key
        }

        # 3) Make the GET request to fetch the plan details
        try:
            response = requests.get(url, headers=headers, timeout=15)
        except requests.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": "Error connecting to eSIM-Go API.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 4) Handle the response
        if response.status_code == 200:
            plan_data = response.json()

            # Optional transformations:
            # For example, formatting volume/price so it matches your style

            # (a) Format volume
            if plan_data.get("unlimited") or plan_data.get("dataAmount", -1) < 0:
                plan_data["formattedVolume"] = "Unlimited"
            else:
                data_mb = plan_data.get("dataAmount", 0)
                if data_mb >= 1024:
                    plan_data["formattedVolume"] = f"{(data_mb / 1024):.1f} GB"
                else:
                    plan_data["formattedVolume"] = f"{data_mb} MB"

            # (b) Format price (example: multiply by 2 to match your logic)
            price = plan_data.get("price", 0)
            plan_data["formattedPrice"] = f"{(price * 2):.2f}"

            return Response(
                {
                    "status": True,
                    "message": "eSIM-Go plan details fetched successfully.",
                    "data": plan_data,
                },
                status=status.HTTP_200_OK
            )
        elif response.status_code == 404:
            return Response(
                {
                    "status": False,
                    "message": f"No eSIM-Go plan found with name '{plan_name}'.",
                },
                status=status.HTTP_404_NOT_FOUND
            )
        else:
            # Some other non-200 status
            return Response(
                {
                    "status": False,
                    "message": "Failed to fetch eSIM-Go plan details.",
                    "error": response.text,
                },
                status=response.status_code
            )
        

class eSIMProfileView(APIView):
    """
    View to fetch eSIM profile details based on the orderNo or ICCID.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["eSIM"],
        summary="Fetch purchased eSIM profile details",
        parameters=[
            OpenApiParameter("orderNo", OpenApiTypes.STR, description="Order number for the eSIM profile e.g. B2210206381924", required=False),
            OpenApiParameter("iccid", OpenApiTypes.STR, description="ICCID for the eSIM", required=False),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=eSIMProfileResponseSerializer,
                description="Profile information retrieved successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="Validation failed for the supplied query parameters.",
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="Unexpected error while contacting the eSIM API.",
            ),
        },
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

                                # Calculate the difference on a scale of 0 - 1
                                item['usageScale'] = 1 - (item['orderUsage'] / item['totalVolume']) if item['totalVolume'] > 0 else 0

                                # Calculate duration left and duration left scale
                                activate_time = item.get('activateTime')
                                total_duration = item.get('totalDuration', 0)
                                if activate_time is not None:
                                    activate_datetime = datetime.strptime(activate_time, "%Y-%m-%dT%H:%M:%S%z")
                                else:
                                    activate_datetime = datetime.now()

                                expiration_datetime = activate_datetime + timedelta(days=total_duration)
                                current_datetime = datetime.now()

                                duration_left = (expiration_datetime - current_datetime.replace(tzinfo=activate_datetime.tzinfo)).total_seconds()
                                
                                # Calculate duration left and format it
                                if duration_left >= 86400:
                                    item['durationLeft'] = f"{duration_left // 86400} days"
                                elif duration_left >= 3600:
                                    item['durationLeft'] = f"{duration_left // 3600} hours"
                                else:
                                    item['durationLeft'] = f"{duration_left // 60} mins"
                                item['durationLeftScale'] = max(0, min(1, duration_left / (total_duration * 86400))) if total_duration > 0 else 0

                                print(item['durationLeft'])
                                print(item['durationLeftScale'])
                                # Convert volume from bytes to GB/MB and format prices
                                volume_bytes = item['totalVolume'] - item['orderUsage']

                                if volume_bytes >= 1024 ** 3:
                                    item["formattedVolumeLeft"] = f"{(volume_bytes / (1024 ** 3)):.1f} GB"
                                else:
                                    item["formattedVolumeLeft"] = f"{(volume_bytes / (1024 ** 2)):.0f} MB"

                                item["formattedPrice"] = f"{((esim_plan.price / 10000) * 2):.2f}"
                            except eSIMPlan.DoesNotExist:
                                item['price'] = None
                        enriched_data.append(item)

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
        

@extend_schema_view(
    get=extend_schema(
        tags=["eSIM"],
        summary="List the authenticated user's eSIM plans",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=eSIMUserPlanListResponseSerializer,
                description="Plans retrieved successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
        },
    ),
    post=extend_schema(
        tags=["eSIM"],
        summary="Create an eSIM plan from a completed payment",
        request=eSIMPlanSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=eSIMUserPlanResponseSerializer,
                description="Plan created successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="Validation failed when creating the plan.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
        },
    ),
)
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

                            # Temporarily pass data to plan object for demonstration
                            plan.usageScale = round(esim['orderUsage'] / esim['totalVolume'], 1) if esim['totalVolume'] > 0 else 0

                            # Calculate duration left and duration left scale
                            activate_time = esim.get('activateTime')
                            total_duration = esim.get('totalDuration', 0)
                            if activate_time is not None:
                                activate_datetime = datetime.strptime(activate_time, "%Y-%m-%dT%H:%M:%S%z")
                            else:
                                activate_datetime = datetime.now()

                            expiration_datetime = activate_datetime + timedelta(days=total_duration)
                            current_datetime = datetime.now()

                            duration_left = (expiration_datetime - current_datetime.replace(tzinfo=activate_datetime.tzinfo)).total_seconds()
                            
                            # Calculate duration left and format it
                            if duration_left >= 86400:
                                plan.durationLeft = f"{duration_left // 86400} days"
                            elif duration_left >= 3600:
                                plan.durationLeft = f"{duration_left // 3600} hours"
                            else:
                                plan.durationLeft = f"{duration_left // 60} mins"
                            
                            # Convert volume from bytes to GB/MB and format prices
                            volume_bytes = esim['totalVolume'] - esim['orderUsage']

                            if volume_bytes >= 1024 ** 3:
                                plan.formattedVolumeLeft = f"{(volume_bytes / (1024 ** 3)):.1f} GB"
                            else:
                                plan.formattedVolumeLeft = f"{(volume_bytes / (1024 ** 2)):.0f} MB"
                            print(plan.durationLeft)
                            print(plan.usageScale)
                            print(plan.formattedVolumeLeft)
                        else:
                            print(f"No eSIM data found for plan {plan.order_no}.")
                    else:
                        print(f"API error for plan {plan.order_no}: {api_response.get('errorMsg', 'Unknown error')}")
                else:
                    print(f"HTTP error {response.status_code} for plan {plan.order_no}: {response.text}")
            except requests.RequestException as e:
                print(f"Error fetching eSIM profile for plan {plan.order_no}: {e}")

            updated_plans.append({
                "id": plan.id,
                "order_no": plan.order_no,
                "name": plan.name,
                "slug": plan.slug,
                "package_code": plan.package_code,
                "activated_on": plan.activated_on,
                "volume_used": plan.volume_used,
                "esim_status": plan.esim_status,
                "duration": plan.duration,
                "currency_code": plan.currency_code,
                "speed": plan.speed,
                "volume": plan.volume,
                "price": plan.price,
                "description": plan.description,
                "seller": plan.seller,
                "location_code": plan.location_code,
                "location_code_lower": plan.location_code.lower(),
                "expires_on": plan.expires_on,
                "smdp_status": plan.smdp_status,
                "duration_unit": plan.duration_unit,
                "support_top_up_type": plan.support_top_up_type,
                "usageScale": plan.usageScale,
                "durationLeft": plan.durationLeft,
                "formattedVolumeLeft": plan.formattedVolumeLeft,
            })

        print(updated_plans)
        return Response({
            "status": True,
            "message": "User eSIM plans fetched successfully.",
            "data": updated_plans,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "status": True,
                "message": "eSIM plan created successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


@extend_schema_view(
    get=extend_schema(
        tags=["eSIM"],
        summary="Retrieve a specific eSIM plan",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=eSIMUserPlanResponseSerializer,
                description="Plan retrieved successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="No plan exists for the supplied identifier.",
            ),
        },
    ),
    put=extend_schema(
        tags=["eSIM"],
        summary="Fully update an eSIM plan",
        request=eSIMPlanSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=eSIMUserPlanResponseSerializer,
                description="Plan updated successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="Validation failed when updating the plan.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="No plan exists for the supplied identifier.",
            ),
        },
    ),
    patch=extend_schema(
        tags=["eSIM"],
        summary="Partially update an eSIM plan",
        request=eSIMPlanSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=eSIMUserPlanResponseSerializer,
                description="Plan updated successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="Validation failed when updating the plan.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="No plan exists for the supplied identifier.",
            ),
        },
    ),
    delete=extend_schema(
        tags=["eSIM"],
        summary="Deactivate an eSIM plan",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="Plan deactivated successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="No plan exists for the supplied identifier.",
            ),
        },
    ),
)
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
        tags=["eSIM"],
        summary="List supported countries",
        parameters=[
            OpenApiParameter("name", OpenApiTypes.STR, description="Name of the country to filter", required=False),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=CountryListResponseSerializer,
                description="Countries retrieved successfully.",
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="The countries file could not be read.",
            ),
        },
    )
    def get(self, request):
        try:
            json_file_path = os.path.join(settings.BASE_DIR, 'static', 'vendor', 'locations', 'countries.json')
            with open(json_file_path, 'r') as file:
                countries = json.load(file)
            
            # Convert alpha_2 to lowercase
            for country in countries:
                country['alpha_2_lower'] = country['alpha_2'].lower()
            
            # Filter by name if query param is provided
            name_filter = request.query_params.get('name')
            if name_filter:
                countries = [country for country in countries if name_filter.lower() in country['name'].lower()]
            
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
        tags=["eSIM"],
        summary="List popular countries",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=CountryListResponseSerializer,
                description="Popular countries retrieved successfully.",
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                response=eSIMBaseResponseSerializer,
                description="The popular countries file could not be read.",
            ),
        },
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