from django.urls import path
from . import views

urlpatterns = [
    path('buildings/', views.BuildingListView.as_view(), name='building-list'),
    path('buildings/<int:pk>/', views.BuildingDetailView.as_view(), name='building-detail'),
    path('route/', views.RouteView.as_view(), name='route'),
]