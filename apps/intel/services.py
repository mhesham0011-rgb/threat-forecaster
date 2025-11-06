from collections import Counter

def compute_indicator_type_breakdown(queryset, limit=5):
    """
    Returns [{"indicator_type": "ip", "count": 12}, ...]
    """
    types = (qs_val or "unknown" for qs_val in queryset.values_list("indicator_type", flat=True))
    c = Counter(types)
    return [{"indicator_type": k, "count": v} for k, v in c.most_common(limit)]
