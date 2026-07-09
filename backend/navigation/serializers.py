from rest_framework import serializers
from .models import Building, Waypoint, Edge, NavigationLog


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = [
            'id', 'name', 'short_name', 'category',
            'description', 'latitude', 'longitude',
            'is_accessible', 'is_active'
        ]


class WaypointSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.name', read_only=True)

    class Meta:
        model = Waypoint
        fields = [
            'id', 'name', 'waypoint_type', 'latitude',
            'longitude', 'building', 'building_name', 'is_active'
        ]


class EdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edge
        fields = [
            'id', 'from_waypoint', 'to_waypoint',
            'distance', 'surface', 'is_accessible', 'is_active'
        ]


class RouteRequestSerializer(serializers.Serializer):
    origin_id = serializers.IntegerField()
    destination_id = serializers.IntegerField()
    accessible_only = serializers.BooleanField(default=False)

    def validate(self, data):
        if data['origin_id'] == data['destination_id']:
            raise serializers.ValidationError(
                'Origin and destination cannot be the same.'
            )
        return data


class RouteStepSerializer(serializers.Serializer):
    waypoint_id = serializers.IntegerField()
    name = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    waypoint_type = serializers.CharField()


class RouteResponseSerializer(serializers.Serializer):
    origin = BuildingSerializer()
    destination = BuildingSerializer()
    steps = RouteStepSerializer(many=True)
    total_distance = serializers.FloatField()
    found = serializers.BooleanField()