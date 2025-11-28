from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Branch
from .api.serializers import BranchBriefSerializer, BranchDetailSerializer
from .api.permissions import IsSuperuserOrReadOnly, IsBranchManagerOrSuperuser
from .api.filters import BranchFilter

from django_filters.rest_framework import DjangoFilterBackend

class BranchViewSet(viewsets.ModelViewSet):
    """
    Branch API:
    - list: /api/branches/?brief=true
    - retrieve: /api/branches/{pk}/
    - create: CEO/superuser only
    - partial_update: branch manager or superuser
    """
    queryset = Branch.objects.select_related("country", "region", "city", "district", "location", "manager").prefetch_related("services").all()
    permission_classes = [IsSuperuserOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BranchFilter
    search_fields = ["name", "code", "contact_person", "phone", "email"]
    ordering_fields = ["name", "code", "created_at", "distance_from_main_km"]
    ordering = ["name"]

    def get_permissions(self):
        # use object-level permission for unsafe object updates
        if self.action in ("partial_update", "update", "destroy"):
            self.permission_classes = [IsBranchManagerOrSuperuser]
        else:
            self.permission_classes = [IsSuperuserOrReadOnly]
        return super().get_permissions()

    def get_serializer_class(self):
        # allow a compact serializer for brief list use
        brief = self.request.query_params.get("brief", "false").lower() in ("1", "true", "yes")
        if self.action == "list" and brief:
            return BranchBriefSerializer
        if self.action in ("create", "update", "partial_update"):
            return BranchDetailSerializer
        # for retrieve and default list, use detail serializer
        return BranchDetailSerializer

    def perform_create(self, serializer):
        # if you want to capture created_by, add here (requires Branch to have created_by)
        serializer.save()

    @action(detail=False, methods=["get"], url_path="nearby")
    def nearby(self, request):
        """
        Optional helper: return branches within radius_km of lat/lng.
        Usage: /api/branches/nearby/?lat=5.6&lng=-0.2&radius_km=10
        This implementation does a simple Haversine filter in Python and is fine for small datasets.
        For heavy usage, use PostGIS.
        """
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius_km = float(request.query_params.get("radius_km", 10))
        if not lat or not lng:
            return Response({"detail": "Provide lat and lng query params"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lat = float(lat); lng = float(lng)
        except ValueError:
            return Response({"detail": "Invalid lat/lng"}, status=status.HTTP_400_BAD_REQUEST)

        # cheap filter: compute distance in DB-unsafe way (could be optimized)
        from math import radians, cos, sin, asin, sqrt
        def haversine(lat1, lon1, lat2, lon2):
            # returns km
            R = 6371.0
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            return R * c

        matches = []
        for b in self.get_queryset().filter(is_active=True):
            if b.latitude is None or b.longitude is None:
                continue
            d = haversine(lat, lng, b.latitude, b.longitude)
            if d <= radius_km:
                matches.append((d, b))

        # sort by distance and serialize
        matches.sort(key=lambda x: x[0])
        branches = [m[1] for m in matches]
        serializer = BranchBriefSerializer(branches, many=True, context={"request": request})
        # include distances as parallel list
        return Response({
            "count": len(branches),
            "radius_km": radius_km,
            "results": serializer.data,
            "distances_km": [round(m[0], 2) for m in matches]
        })
