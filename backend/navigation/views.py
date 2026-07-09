from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from .models import Building, NavigationLog
from .serializers import (
    BuildingSerializer,
    RouteRequestSerializer,
    RouteResponseSerializer,
)
from .dijkstra import get_route


class BuildingListView(APIView):
    """
    Public endpoint — returns all active buildings for the map.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        buildings = Building.objects.filter(is_active=True)
        serializer = BuildingSerializer(buildings, many=True)
        return Response(serializer.data)


class BuildingDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            building = Building.objects.get(pk=pk, is_active=True)
        except Building.DoesNotExist:
            return Response(
                {'error': 'Building not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(BuildingSerializer(building).data)


@method_decorator(
    ratelimit(key='ip', rate='60/m', method='POST', block=True),
    name='dispatch'
)
class RouteView(APIView):
    """
    Core navigation endpoint.
    Accepts origin and destination building IDs.
    Returns the shortest path as an ordered list of waypoints.
    Rate limited to 60 requests/minute per IP.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RouteRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        origin_id = serializer.validated_data['origin_id']
        destination_id = serializer.validated_data['destination_id']
        accessible_only = serializer.validated_data['accessible_only']

        try:
            origin = Building.objects.get(pk=origin_id, is_active=True)
            destination = Building.objects.get(pk=destination_id, is_active=True)
        except Building.DoesNotExist:
            return Response(
                {'error': 'One or both buildings not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        total_distance, waypoints = get_route(origin, destination, accessible_only)

        found = bool(waypoints)

        # Log the request (anonymized — no GPS coords stored)
        NavigationLog.objects.create(
            user=request.user,
            origin=origin,
            destination=destination,
            was_successful=found,
        )

        steps = []
        for wp in waypoints:
            steps.append({
                'waypoint_id': wp.id,
                'name': wp.name or '',
                'latitude': wp.latitude,
                'longitude': wp.longitude,
                'waypoint_type': wp.waypoint_type,
            })

        return Response({
            'origin': BuildingSerializer(origin).data,
            'destination': BuildingSerializer(destination).data,
            'steps': steps,
            'total_distance': round(total_distance, 2) if total_distance else 0,
            'found': found,
        })