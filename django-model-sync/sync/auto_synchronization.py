import structlog as logging

from apps.b3_migration.model_descriptors.utils import get_buddy_class
from apps.b3_migration.sync.utils import sync_source_and_target_models
from apps.b3_migration.sync.auto_synchronization_base import \
    AutoSynchronizationBase

logger = logging.getLogger(__name__)


class ModelToModelAutoSynchronizationMixin(AutoSynchronizationBase):
    """
    Mixin added to model classes for auto synchronization. This works for
    models that map on the instance level not the field level


    HOW TO USE:
        1. Have your model inherit from this mixin before models.Model -and
            any other parent class that overrides :function: `delete()`
            and :function: `save()`- since it needs to have precedence over
            such classes
        2. Override :function: `get_source_and_target_descriptors()`
        3. IF your model requires a special check in :function: `save()` for
            whether the instance is being updated or created, implement
            :function: `exists_in_db()` that returns a boolean signifying if
            the instance exists in the database -and thus is being updated
            not created-. Example case would be if you override the pk and thus
            checking the existance of a pk on the current instance would always
            be true regardless of whether it is an update or create that is
            being performed


    PRECAUTION:
        > this does not take into account operations that neither call
            :function: `delete()` or :function: `save()`
            for instance: :function: `bulk_create()` or :function: `update()`
            or -obviously- any raw SQL queries...
    """

    def _pre_save(self, *args, update=False, target=False, **kwargs):
        """
        Pre-save, check if deleted, then don't do anything i.e. don't
        allow :function: `_post_save()` to run by returning False
        :return bool implying whether or not to run :function: `_post_save()`
        """
        # :model: `OrganizationBillingAddress` and
        # `OrganizationShippingAddress` are to be deleted from project but
        # since they both inherit from :model: `AbstractAddress` we need to
        # prevent auto sync for them. The other option would be to augment
        # every address model with this mixin, but that seems WET and would
        # lead to more changes once these two models are removed from the
        # project
        # TODO: remove once these models are deleted from the project
        if self.__class__.__name__ in [
            'OrganizationBillingAddress',
            'OrganizationShippingAddress'
        ]:
            return False

        if getattr(self, 'deleted_date', False):
            return False

        return True

    def _post_save(self, *args, update=False, target=False, **kwargs):
        """
        Overriding :function: `_post_save()` to perform sync between old and
        new models.

        The model that initiates the saving adds a :kwarg: `target=True` to the
        call for :function: `save()` of the target model so as not to loop
        infinitely from one model to the other.

        Steps:
            1. If self is not the target -and thus the initiator-,
                call sync function
        """
        if not target:
            source_descriptor, target_descriptor = \
                self.get_source_and_target_descriptors()
            sync_source_and_target_models(
                self,
                source_descriptor,
                target_descriptor,
                get_buddy_class(target_descriptor),
                'AUTO-SYNC',
                update=update
            )

    def _pre_delete(self, *args, target=False, **kwargs):
        """
        Overriding :function: `_pre_delete()` to perform sync between old and
        new models.

        The model that initiates the deletion adds a :kwarg: `target=True` to
        the call for :function: `delete()` of the target model so as not to
        loop infinitely from one model to the other.

        Steps:
            if self is the target:
                return
            else
                1. Get source and target descriptors
                2. Use descriptors to get target instance
                3. Set :kwarg: `target=True`
                4. Check if a buddy instance exists - thus a target also exists
                5. Delete buddy instance
                6. Delete target
        :return bool implying whether or not to run :function: `_post_delete()`
        """
        if not target:
            source_descriptor, target_descriptor = \
                self.get_source_and_target_descriptors()

            source_related_name_in_buddy = source_descriptor[
                'related_name_in_buddy']

            if hasattr(self, source_related_name_in_buddy):
                buddy_instance = getattr(self, source_related_name_in_buddy)

                target_field_name_in_buddy = target_descriptor[
                    'field_name_in_buddy']
                target_instance = getattr(
                    buddy_instance, target_field_name_in_buddy)

                logger.debug(f'AUTO-SYNC: Starting delete for buddy '
                             f'instance: {buddy_instance}')

                buddy_instance.delete()

                logger.debug(f'AUTO-SYNC: Completed delete for buddy '
                             f'instance: {buddy_instance}')

                target_instance.delete(*args, target=True, **kwargs)
        return True

    def _post_delete(self, *args, target=False, **kwargs):
        """
        Do nothing after deletion
        """

    def get_source_and_target_descriptors(self):
        """
        Gets the source and target descriptors - Needed for sync.

        :return source_descriptor, target_descriptor:
        """
        raise NotImplementedError(
            'AutoSynchronizationMixin requires '
            'the function get_source_and_target_descriptors() to '
            'be implemented'
        )

    def exists_in_db(self):
        """
        Checks if `self` is already in database. This is used with the
        AutoSyncMixin for checking on save whether it is an update or a create
        """
        return self.__class__.objects.filter(pk=self.pk).exists()
