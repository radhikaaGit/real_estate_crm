import django_filters

from .models import Lead


class LeadFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Lead.Status.choices)
    lead_source = django_filters.ChoiceFilter(choices=Lead.Source.choices)

    class Meta:
        model = Lead
        fields = ["status", "lead_source", "assigned_to"]