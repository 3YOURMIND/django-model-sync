from django.db.utils import IntegrityError

from apps.b3_migration.factories.switch_factory import SwitchFactory
from apps.b3_organization.models.organization import Organization
from apps.b3_tests.testcases import B3TestCase


class SwitchTests(B3TestCase):
    def setUp(self):
        super().setUp()

        self.organization = Organization.objects.first()
        self.organization.showname = '3YOURMIND'
        self.organization.save()
        self.switch = SwitchFactory(
            feature='new_checkout',
            organization=self.organization,
        )

    def test_str(self):
        """Test string representation of Switch"""
        self.assertEqual(
            self.switch.__str__(),
            '3YOURMIND: new_checkout - Active'
        )

    def test_uniqueness_constraints(self):
        """
        Asserts that :field: `organization` and :field: `feature`
        are unique together
        """
        switch = SwitchFactory.build(
            feature='new_checkout',
            organization=self.organization,
        )
        self.assertRaises(
            IntegrityError,
            switch.save
        )
