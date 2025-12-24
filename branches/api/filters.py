import django_filters
from branches.models import Branch

class BranchFilter(django_filters.FilterSet):
    country = django_filters.NumberFilter(field_name="country__id")
    country_code = django_filters.CharFilter(field_name="country__code", lookup_expr="iexact")
    region = django_filters.NumberFilter(field_name="region__id")
    city = django_filters.NumberFilter(field_name="city__id")
    is_active = django_filters.BooleanFilter(field_name="is_active")
    is_main = django_filters.BooleanFilter(field_name="is_main")
    service = django_filters.CharFilter(method="filter_by_service", label="service (code or id)")

    class Meta:
        model = Branch
        fields = ["country", "country_code", "region", "city", "is_active", "is_main"]

    def filter_by_service(self, queryset, name, value):
        # accept either numeric id or service code
        if not value:
            return queryset
        if value.isdigit():
            return queryset.filter(services__id=int(value))
        return queryset.filter(services__code__iexact=value)
