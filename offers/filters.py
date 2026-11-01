import datetime
from django.db.models import Q
from django.utils import timezone
import django_filters

from .models import Customer, GiftItem


class CustomerFilter(django_filters.FilterSet):
    """
    FilterSet for Customer model supporting:
    - Multiple gift selection (by ID or name, list or comma-separated)
    - Date filtering (start_date, end_date, preset 'today')
    - Search and status filters
    """
    lucky_draw_system = django_filters.NumberFilter(field_name="lucky_draw_system_id")
    lucky_draw_system_id = django_filters.NumberFilter(field_name="lucky_draw_system_id")
    start_date = django_filters.DateFilter(method="filter_by_date_range")
    end_date = django_filters.DateFilter(method="filter_by_date_range")
    filter = django_filters.CharFilter(method="filter_by_preset")
    gift = django_filters.ModelMultipleChoiceFilter(
        queryset=GiftItem.objects.all(),
        method="filter_by_gift",
        label="Gift (Multiple Selection)",
    )
    gifts = django_filters.CharFilter(method="filter_by_gift")
    gift_id = django_filters.CharFilter(method="filter_by_gift")
    gift_ids = django_filters.CharFilter(method="filter_by_gift")
    customer_name = django_filters.CharFilter(lookup_expr="icontains")
    phone_number = django_filters.CharFilter(lookup_expr="icontains")
    shop_name = django_filters.CharFilter(lookup_expr="icontains")
    sold_area = django_filters.CharFilter(lookup_expr="icontains")
    region = django_filters.CharFilter(lookup_expr="iexact")
    imei = django_filters.CharFilter(lookup_expr="icontains")
    phone_model = django_filters.CharFilter(lookup_expr="icontains")
    sale_status = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Customer
        fields = [
            "lucky_draw_system",
            "lucky_draw_system_id",
            "start_date",
            "end_date",
            "filter",
            "gift",
            "gifts",
            "gift_id",
            "gift_ids",
            "customer_name",
            "phone_number",
            "shop_name",
            "sold_area",
            "region",
            "imei",
            "phone_model",
            "sale_status",
        ]

    def filter_by_date_range(self, queryset, name, value):
        if getattr(self, "_date_range_applied", False):
            return queryset
        self._date_range_applied = True

        start_date_val = self.data.get("start_date")
        end_date_val = self.data.get("end_date")

        start = None
        end = None

        if start_date_val:
            try:
                start = datetime.datetime.strptime(str(start_date_val).strip(), "%Y-%m-%d").date()
            except ValueError:
                start = None

        if end_date_val:
            try:
                end = datetime.datetime.strptime(str(end_date_val).strip(), "%Y-%m-%d").date()
            except ValueError:
                end = None

        if start and end:
            if start == end:
                return queryset.filter(date_of_purchase=start)
            return queryset.filter(date_of_purchase__gte=start, date_of_purchase__lte=end)
        elif start:
            return queryset.filter(date_of_purchase=start)
        elif end:
            return queryset.filter(date_of_purchase__lte=end)

        return queryset

    def filter_by_preset(self, queryset, name, value):
        if str(value).lower() == "today":
            today_date = timezone.now().date()
            return queryset.filter(date_of_purchase=today_date)
        return queryset

    def filter_by_gift(self, queryset, name, value):
        if getattr(self, "_gift_filter_applied", False):
            return queryset
        self._gift_filter_applied = True

        raw_gift_params = []
        if hasattr(self.data, "getlist"):
            for key in ("gift", "gifts", "gift_id", "gift_ids", "gift[]", "gifts[]", "gift_ids[]"):
                raw_gift_params.extend(self.data.getlist(key))
        elif isinstance(self.data, dict):
            for key in ("gift", "gifts", "gift_id", "gift_ids", "gift[]", "gifts[]", "gift_ids[]"):
                val = self.data.get(key)
                if isinstance(val, (list, tuple)):
                    raw_gift_params.extend(val)
                elif val:
                    raw_gift_params.append(val)

        if value:
            if hasattr(value, "values_list"):
                raw_gift_params.extend(value.values_list("id", flat=True))
            elif isinstance(value, (list, tuple)):
                for v in value:
                    raw_gift_params.append(getattr(v, "id", v))
            elif getattr(value, "id", None):
                raw_gift_params.append(value.id)
            elif str(value) not in raw_gift_params:
                raw_gift_params.append(str(value))

        gift_tokens = []
        for val in raw_gift_params:
            if val:
                for part in str(val).split(","):
                    cleaned = part.strip().strip("[]'\"")
                    if cleaned and cleaned not in gift_tokens:
                        gift_tokens.append(cleaned)

        if not gift_tokens:
            return queryset

        gift_ids = []
        gift_names = []
        filter_no_gift = False

        for token in gift_tokens:
            if token.lower() in ("none", "no_gift", "no-gift", "null", "empty", "no gift"):
                filter_no_gift = True
            elif token.isdigit():
                gift_ids.append(int(token))
            else:
                gift_names.append(token)

        gift_q = Q()
        if gift_ids:
            gift_q |= Q(gift__id__in=gift_ids)
        if gift_names:
            gift_q |= Q(gift__name__in=gift_names)
        if filter_no_gift:
            gift_q |= Q(gift__isnull=True)

        if gift_q:
            return queryset.filter(gift_q).distinct()

        return queryset

    def get_date_label(self, today_date=None):
        start_date_param = self.data.get("start_date")
        end_date_param = self.data.get("end_date")
        filter_param = self.data.get("filter")

        if start_date_param and end_date_param:
            return f"{start_date_param}" if start_date_param == end_date_param else f"{start_date_param}_to_{end_date_param}"
        elif start_date_param:
            return f"{start_date_param}"
        elif end_date_param:
            return f"to_{end_date_param}"
        elif filter_param == "today":
            today = today_date or timezone.now().date()
            return f"{today}"
        return "all"
