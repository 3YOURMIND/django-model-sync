import factory

from apps.b3_migration.models.switch import Switch
from apps.b3_organization.models.organization import Organization


class SwitchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Switch

    organization = factory.LazyFunction(
        Organization.objects.order_by('?').first)
    feature = factory.Iterator(
        [feature for feature, _ in Switch.FEATURE_CHOICES])
    active = True
