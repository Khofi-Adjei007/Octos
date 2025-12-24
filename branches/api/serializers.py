from rest_framework import serializers
from branches.models import (
    Branch, Country, Region, City, District, Location
)

# Small nested serializers for reuse
class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("id", "code", "name")

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ("id", "name")

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name")

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ("id", "name")

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "name", "type", "latitude", "longitude")


# Manager / employee representation — don't assume employee fields, use str()
class ManagerSimpleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    display = serializers.CharField()

# Compact serializer used for attendants/cashiers UI
class BranchBriefSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    region = RegionSerializer(read_only=True)
    city = CitySerializer(read_only=True)
    services = serializers.SlugRelatedField(many=True, read_only=True, slug_field="code")

    class Meta:
        model = Branch
        fields = (
            "id", "code", "name", "slug",
            "country", "region", "city",
            "is_active", "is_main",
            "services", "phone", "distance_from_main_km"
        )

# Full admin serializer
class BranchDetailSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    region = RegionSerializer(read_only=True)
    city = CitySerializer(read_only=True)
    district = DistrictSerializer(read_only=True)
    location = LocationSerializer(read_only=True)

    manager = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    # allow write for simple fields via ids
    country_id = serializers.PrimaryKeyRelatedField(
        source="country", queryset=Country.objects.all(), write_only=True, required=False
    )
    region_id = serializers.PrimaryKeyRelatedField(
        source="region", queryset=Region.objects.all(), write_only=True, required=False
    )
    city_id = serializers.PrimaryKeyRelatedField(
        source="city", queryset=City.objects.all(), write_only=True, required=False
    )
    district_id = serializers.PrimaryKeyRelatedField(
        source="district", queryset=District.objects.all(), write_only=True, required=False
    )
    location_id = serializers.PrimaryKeyRelatedField(
        source="location", queryset=Location.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = Branch
        fields = (
            "id", "code", "name", "slug",
            "country", "region", "city", "district", "location",
            "country_id", "region_id", "city_id", "district_id", "location_id",
            "manager", "contact_person", "phone", "email",
            "latitude", "longitude", "services", "service_ids",
            "opening_hours", "is_main", "is_active",
            "distance_from_main_km",
            "meta", "created_at", "updated_at",
        )

    def get_manager(self, obj):
        m = getattr(obj, "manager", None)
        if not m:
            return None
        return {"id": getattr(m, "pk", None), "display": str(m)}
