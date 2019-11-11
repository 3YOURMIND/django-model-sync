import typing as t
import structlog as logging
from contextlib import contextmanager
from django.db import models

from apps.b3_migration.model_descriptors.utils import (
    get_model_class,
)
from apps.b3_migration.sync.auto_synchronization_base \
    import AutoSynchronizationBase

logger = logging.getLogger(__name__)


def sync_source_and_target_models(
    source_instance,
    source_model_descriptor,
    target_model_descriptor,
    buddy_model_class,
    logging_prefix,
    update=False,
):
    """
    Create/update an instance of the target model based on the source model

    1. Using the target model's :dict: `fields_mapping` (
            which maps the names of fields in the source model to the name of
            fields in the new model
            e.g.
                fields_mapping = {'postcode': 'zip_code'}

                             leads to

                target_model_dict['zip_code'] = \
                    getattr(source_instance, 'postcode']
        ),
        populate a new :dict: `target_model_dict` with values
        from :model instance: `source_instance`
    2. Using the target model's :list of dicts: `fields_funcs` run the
    functions on the source instance and use the return value to populate
    :param buddy_model_class:
    :dict: `target_model_dict`

    When calling :function: `save()` on the target instance the
    :kwarg: `target=True` is passed to tell :function: `save()` that the
    instance being saved is the target of sync,
    not the initiator and thus should not propagate further calls
    to the sync function (function we are currently inside)

    :param source_instance: instance of the source model
    :param source_model_descriptor: source model descriptor dictionary
    :param target_model_descriptor: target model descriptor dictionary
    :param logging_prefix: string prefix used in log messages, this should
        indicate the context of the function caller e.g. INIT-SYNC for
        the initial sync
    :param update: boolean identifying whether it is an update or a create
    :return instance of the new model
    """
    logger.debug(f'{logging_prefix}: Starting syncing instance: '
                 f'{source_instance}. Instance class:'
                 f' {source_instance.__class__.__name__}. Is update: {update}')
    target_model_dict = {}
    fields_mapping = target_model_descriptor.get('fields_mapping', {})
    fields_optional = target_model_descriptor.get('fields_optional', [])
    fields_funcs = target_model_descriptor.get('fields_funcs', [])

    logger.debug(f'{logging_prefix}: Starting building target dictionary')
    logger.debug(f'{logging_prefix}: Starting using fields mapping')

    for source_field_name, target_field_name in fields_mapping.items():
        if hasattr(source_instance, source_field_name):
            target_model_dict[target_field_name] = getattr(
                source_instance, source_field_name)
        elif source_field_name in fields_optional:
            pass
        else:
            raise KeyError(f'{source_field_name}')
    logger.debug(f'{logging_prefix}: Completed using fields mapping')

    logger.debug(f'{logging_prefix}: Starting using fields functions')
    for key, func, optional in fields_funcs:
        if optional and not hasattr(source_instance, key):
            continue
        target_model_dict[key] = func(source_instance)
    logger.debug(f'{logging_prefix}: Completed using fields functions')

    logger.debug(f'{logging_prefix}: Completed building target dictionary, '
                 f'target dictionary: {target_model_dict}')

    source_related_name_in_buddy = source_model_descriptor[
        'related_name_in_buddy']

    if update and hasattr(source_instance, source_related_name_in_buddy):
        logger.debug(f'{logging_prefix}: Starting update on'
                     f'target instance because a buddy instance exists')

        buddy_instance = getattr(
            source_instance, source_related_name_in_buddy)

        target_field_name_in_buddy = target_model_descriptor[
            'field_name_in_buddy']
        target_instance = getattr(buddy_instance, target_field_name_in_buddy)

        update_instance(target_instance, target_model_dict)
        target_instance.refresh_from_db()

        logger.debug(f'{logging_prefix}: Completed update on target instance')
    else:
        logger.debug(f'{logging_prefix}: Starting creation of target instance')

        target_model_class = get_model_class(target_model_descriptor)
        target_instance = target_model_class(**target_model_dict)

        if isinstance(target_instance, AutoSynchronizationBase):
            # Prevents ending up in synchronization loop
            target_instance.save(target=True)
        else:
            # target_instance does not sync anymore. Normal save is enough.
            target_instance.save()

        logger.debug(f'{logging_prefix}: Completed creation of target '
                     f'instance')

        logger.debug(f'{logging_prefix}: Starting creation of buddy instance')

        target_field_name_in_buddy = target_model_descriptor[
            'field_name_in_buddy']
        source_field_name_in_buddy = source_model_descriptor[
            'field_name_in_buddy']

        buddy_model_class.objects.create(**{
            f'{source_field_name_in_buddy}_id': source_instance.pk,
            f'{target_field_name_in_buddy}_id': target_instance.pk})

        logger.debug(f'{logging_prefix}: Completed creation of buddy instance')

    logger.debug(f'{logging_prefix}: Completed sync. '
                 f'Target instance: {target_instance}')
    return target_instance


def update_instance(instance, update_dict):
    """
    Update and instance of model based on an update dictionary
    :param instance: instance being updated
    :param update_dict: dictionary with update keys, values
    """
    for field_name, field_val in update_dict.items():
        setattr(instance, field_name, field_val)
    instance.save(target=True)


@contextmanager
def disable_auto_sync(*model_classes: t.Type[models.Model]):
    """
    Allows to temporarily disable auto-sync for given models. Accepts one or
    many model classes.

    Used, for example, in _tests while creating test fixtures.

    Usage:

        with disable_auto_sync(Partner):
            partner = PartnerFactory(
                is_managed_account=False,
                invoice_enabled=True,
                pay_in_store_enabled=False,
                po_payment_enabled=True,
                volkswagen_payment_enabled=False,
                nets_payment_enabled=False,
            )

    In this case, PartnerPaymentMethod for 'invoice' and 'po_upload' will not
    be auto-created
    """
    original_pre_saves_deletes = []

    for model_class in model_classes:
        original_pre_saves_deletes.append(
            (model_class,
             getattr(model_class, '_pre_save', None),
             getattr(model_class, '_post_save', None),
             getattr(model_class, '_pre_delete', None),
             getattr(model_class, '_post_delete', None))
        )

        model_class._pre_save = model_class._pre_delete = \
            model_class._post_save = model_class._post_delete = \
            lambda *args, **kwargs: None
    yield model_classes

    for model_class, pre_save, post_save, pre_delete, post_delete \
            in original_pre_saves_deletes:
        model_class._pre_save = pre_save
        model_class._post_save = post_save
        model_class._pre_delete = pre_delete
        model_class._post_delete = post_delete
