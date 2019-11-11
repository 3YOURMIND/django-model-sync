from django.db import models
from apps.b3_organization.utils import get_current_org


class Switch(models.Model):
    """A feature switch.
    Switches are active, or inactive, per organization.
    """
    NEW_USER_PANEL = 'new_user_panel'
    NEW_BASKET = 'new_basket'
    NEW_SALES_TRANSACTION = 'sales_transaction'
    NEW_PART_REQUIREMENTS = 'part_requirements'

    FEATURE_CHOICES = (
        (NEW_USER_PANEL, 'New UserPanel'),
        (NEW_BASKET, 'New Basket'),
        (NEW_SALES_TRANSACTION, 'Sales Transaction'),
        (NEW_PART_REQUIREMENTS, 'Part Requirements')
    )

    organization = models.ForeignKey(
        'b3_organization.Organization',
        related_name='switches',
        verbose_name='Organization',
        on_delete=models.CASCADE,
    )
    feature = models.CharField(
        choices=FEATURE_CHOICES,
        max_length=32,
        help_text='Feature being switched/toggled',
        verbose_name='Feature'
    )
    active = models.BooleanField(
        default=False,
        help_text='Is this switch active?',
        verbose_name='Active',
    )
    note = models.TextField(
        blank=True,
        help_text='Switch description',
        verbose_name='Note',
    )
    creation_date = models.DateTimeField(
        auto_now_add=True,
        help_text='Date when this Switch was created.',
        verbose_name='Created',
    )
    last_modified = models.DateTimeField(
        auto_now=True,
        help_text='Date when this Switch was last modified.',
        verbose_name='Last Modified',
    )

    class Meta:
        verbose_name = 'Switch'
        verbose_name_plural = 'Switches'
        unique_together = ('organization', 'feature')

    def __str__(self):
        """
        String representation of a switch
        :return: Organization name and feature name
        """
        active = 'Active' if self.active else 'Inactive'
        feature = self.get_feature_display()
        return f'{self.organization.showname}: {feature} - {active}'

    @classmethod
    def is_active(cls, feature, organization=None):
        organization = organization or get_current_org()
        try:
            switch = Switch.objects.get(
                feature=feature,
                organization=organization
            )
            return switch.active
        except Switch.DoesNotExist:
            return False
