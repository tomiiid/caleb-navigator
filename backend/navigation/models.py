from django.db import models


class Building(models.Model):
    """Represents a physical building or point of interest on campus"""
    
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('administrative', 'Administrative'),
        ('hostel', 'Hostel'),
        ('facility', 'Facility'),
        ('religious', 'Religious'),
        ('sport', 'Sport'),
        ('medical', 'Medical'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    is_accessible = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Waypoint(models.Model):
    """
    A node on the campus graph.
    Can be a building entrance, pathway junction, or landmark.
    """

    TYPE_CHOICES = [
        ('entrance', 'Building Entrance'),
        ('junction', 'Pathway Junction'),
        ('parking', 'Parking Area'),
        ('landmark', 'Landmark'),
    ]

    name = models.CharField(max_length=200, blank=True)
    waypoint_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='junction')
    latitude = models.FloatField()
    longitude = models.FloatField()
    building = models.ForeignKey(
        Building,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='waypoints'
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name or f"Waypoint ({self.latitude}, {self.longitude})"

    class Meta:
        ordering = ['name']


class Edge(models.Model):
    """
    A connection between two waypoints — the edges of the campus graph.
    Used by Dijkstra's algorithm to calculate shortest paths.
    """

    SURFACE_CHOICES = [
        ('footpath', 'Footpath'),
        ('road', 'Road'),
        ('indoor', 'Indoor Corridor'),
    ]

    from_waypoint = models.ForeignKey(
        Waypoint,
        on_delete=models.CASCADE,
        related_name='edges_from'
    )
    to_waypoint = models.ForeignKey(
        Waypoint,
        on_delete=models.CASCADE,
        related_name='edges_to'
    )
    distance = models.FloatField(help_text='Distance in meters')
    surface = models.CharField(max_length=20, choices=SURFACE_CHOICES, default='footpath')
    is_accessible = models.BooleanField(default=True, help_text='Wheelchair accessible')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.from_waypoint} → {self.to_waypoint} ({self.distance}m)"

    class Meta:
        unique_together = ['from_waypoint', 'to_waypoint']


class NavigationLog(models.Model):
    """
    Anonymized log of navigation requests for audit and analytics.
    No personal location data stored — only origin/destination building IDs.
    """

    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='navigation_logs'
    )
    origin = models.ForeignKey(
        Building,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs_as_origin'
    )
    destination = models.ForeignKey(
        Building,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs_as_destination'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    was_successful = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.origin} → {self.destination} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']