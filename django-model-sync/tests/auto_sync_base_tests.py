from django.core.exceptions import ObjectDoesNotExist

from apps.b3_migration.model_descriptors.utils import (
    get_model_class, get_buddy_class)


class AutoSyncBaseTests:
    """
    Base class for testing auto synchronization between old and new models

    Attribute comments:

        old_models_descriptors_and_factories: [(dict, Factory Class),]
            list of sets of the descriptor dictionary and factory classes
            of the old model
            e.g. [
                (shipping_address_descriptor_dict, ShippingAddressFactory),
                (billing_address_descriptor_dict, BillingAddressFactory),
                (user_address_descriptor_dict, UserAddressFactory),
            ]

        new_model_descriptor: dict
            descriptor dict for new model

        new_model_factory: Factory Class
            New model's factory class

        update_old_to_new_dict: dict
            dictionary of the fields to update from old model to new model
            when testing and the values to update to
            e.g. {'postcode': '10696', 'first_name': 'Jakob'}

        update_new_to_old_dict: dict
            dictionary of the fields to update from new model to old model
            when testing and the values to update to
            e.g. {'zip_code': '10696', 'first_name': 'Jakob'}
    """
    old_models_descriptors_and_factories = [({}, None), ]
    new_model_descriptor = {}
    new_model_factory = None
    update_old_to_new_dict = {}
    update_new_to_old_dict = {}
    switch = None

    def tearDown(self):
        super().tearDown()

        for old_model_descriptor, _ in \
                self.old_models_descriptors_and_factories:
            old_model_class = get_model_class(old_model_descriptor)
            old_model_class.objects.all().delete()

        new_model_class = get_model_class(self.new_model_descriptor)
        new_model_class.objects.all().delete()

    def _create_and_assert_in_sync(
        self,
        source_model_factory_class,
        target_model_descriptors,
    ):
        """
        Create instances of the old model and then assert sync
        :param source_model_factory_class: Factory class for old model
                                    e.g. ShippingAddressFactory
        """
        target_model_count_before_sync = 0
        buddy_model_count_before_sync = 0
        for target_model_descriptor in target_model_descriptors:
            target_model_class = get_model_class(target_model_descriptor)
            buddy_model_class = get_buddy_class(target_model_descriptor)
            target_model_count_before_sync += \
                target_model_class.objects.count()
            buddy_model_count_before_sync += buddy_model_class.objects.count()

        source_model_factory_class()

        target_model_count_after_sync = 0
        for target_model_descriptor in target_model_descriptors:
            target_model_class = get_model_class(target_model_descriptor)
            buddy_model_class = get_buddy_class(target_model_descriptor)
            target_model_count_after_sync += target_model_class.objects.count()

        buddy_model_count_after_sync = buddy_model_class.objects.count()

        self.assertEqual(
            buddy_model_count_before_sync + 1, buddy_model_count_after_sync)
        self.assertEqual(
            target_model_count_before_sync + 1, target_model_count_after_sync)

    def _update_and_assert_in_sync(
        self,
        source_descriptor,
        source_factory_class,
        target_descriptors,
        update_dict,
        without_target_existing=False,
    ):
        """
        1. Check if instance of the old model exists, if not, create one
        2. Perform update
        3. Assert sync
        :param source_descriptor: Descriptor dict for source model
        :param source_factory_class: Factory class for source model
        :param target_descriptors: List of descriptor dict for target models
        :param update_dict: dictionary of the fields to update and their values
        :param without_target_existing: boolean signifying whether to test
            update with or without a target instance already in sync
        """
        source_class = get_model_class(source_descriptor)
        source_model_manager = source_descriptor.get(
            'model_manager', 'objects')

        if without_target_existing:
            # Save instance with :kwarg: `target=True` to prevent auto sync
            source_instance = source_factory_class.build()
            source_instance.save(target=True)
        else:
            source_instance = source_factory_class()

        for field, field_val in update_dict.items():
            if hasattr(source_instance, field):
                setattr(source_instance, field, field_val)
            else:
                raise KeyError(f'{source_instance} has no key {field}')
        source_instance.save()
        # This is needed to refresh related_names.
        # Using :function: `refresh_from_db()` here would not be sufficient
        # since it does not refresh related_names
        source_instance = getattr(source_class, source_model_manager).get(
            pk=source_instance.pk
        )

        related_name_in_buddy = source_descriptor[
            'related_name_in_buddy']
        buddy_instance = getattr(
            source_instance, related_name_in_buddy)

        target_descriptor = None
        for current_target_descriptor in target_descriptors:
            target_field_name_in_buddy = current_target_descriptor[
                'field_name_in_buddy']
            target_instance = getattr(
                buddy_instance,
                target_field_name_in_buddy)
            if target_instance:
                target_descriptor = current_target_descriptor
                break

        if not target_descriptor:
            raise ValueError(
                'Target descriptor should not be none, this means that'
                ' we could not figure out which one of the passed target'
                'descriptors is the correct one')

        target_class = get_model_class(target_descriptor)
        target_model_manager = target_descriptor.get(
            'model_manager', 'objects')

        # Python allows for setting of new attributes to an object at runtime
        # these attributes might not be in the model's fields.
        # Thus, if any code mutates the object by adding new attributes that
        # exists in the the other model's fields, the test could falsely pass.
        # Thus, we retrieve the instance from DB again before asserting sync
        source_instance = getattr(source_class, source_model_manager).get(
            pk=source_instance.pk
        )
        target_instance = getattr(target_class, target_model_manager).get(
            pk=target_instance.pk
        )
        # Do not put code between the source and target instance retreivals
        # and call for assert sync -- check explanation above.
        self._assert_sync(
            source_instance,
            target_instance,
            source_descriptor,
            target_descriptor,
        )

    def _assert_sync(
        self,
        source_instance,
        target_instance,
        source_descriptor,
        target_descriptor,
    ):
        """
        Asserts that :instance of model: `instance_old` and
        :instance of model: `instance_new` are in sync over the
        fields in `field_mapping` unless the field is optional then the check
        is not done since the field exists in one instance but not the other

        :param source_instance: instance of the source model
        :param target_instance: instance of the target model
        :param source_descriptor: source model descriptor
        :param target_descriptor: target model descriptor
        """
        fields_mapping = target_descriptor['fields_mapping']

        for field_source, field_target in fields_mapping.items():
            fields_optional_source = source_descriptor.get(
                'fields_optional', [])
            fields_optional_target = target_descriptor.get(
                'fields_optional', [])

            if (
                hasattr(source_instance, field_source) and
                hasattr(target_instance, field_target)
            ):
                self.assertEqual(
                    getattr(source_instance, field_source),
                    getattr(target_instance, field_target))
            elif (
                field_source in fields_optional_source or
                field_target in fields_optional_target
            ):
                pass
            else:
                # Reaching this else suggests that one or both fields are not
                # in the instance(s) and thus we can call them to
                # raise an :error: `AttributeError`
                getattr(source_instance, field_source)
                getattr(target_instance, field_target)

    def _delete_and_assert_in_sync(
        self,
        source_descriptor,
        source_factory,
        target_descriptors=[],
        without_target_existing=False,
    ):
        """
        Delete source instance and assert that the target instance is deleted
        as well
        :param source_descriptor: Source model descriptor
        :param source_factory: Source model factory
        :param target_descriptors: Target models descriptors, can be empty if
            :kwarg: without_target_existing=True
        :param without_target_existing: boolean signifying whether to test
            delete with or without a target instance already in sync
        """
        if not target_descriptors and not without_target_existing:
            raise Exception('target_descriptors and without_target_existing'
                            ' cannot both be empty/False at the same time')

        if without_target_existing:
            source_instance = source_factory.build()
            source_instance.save(target=True)
        else:
            source_instance = source_factory()
            related_name_in_buddy = source_descriptor[
                'related_name_in_buddy']

            buddy_instance = getattr(source_instance, related_name_in_buddy)

            for target_descriptor in target_descriptors:
                target_field_name_in_buddy = target_descriptor[
                    'field_name_in_buddy']
                target_instance = getattr(
                    buddy_instance, target_field_name_in_buddy)
                if target_instance:
                    break
            self.assertTrue(target_instance)

        source_instance.delete()

        source_class = get_model_class(source_descriptor)
        source_model_manager = source_descriptor.get(
            'model_manager', 'objects')
        with self.assertRaises(ObjectDoesNotExist):
            getattr(source_class, source_model_manager).get(
                pk=source_instance.pk)

        if not without_target_existing:
            target_class = get_model_class(target_descriptor)
            target_model_manager = target_descriptor.get(
                'model_manager', 'objects')

            with self.assertRaises(ObjectDoesNotExist):
                getattr(target_class, target_model_manager).get(
                    pk=target_instance.pk)

            with self.assertRaises(ObjectDoesNotExist):
                buddy_instance.__class__.objects.get(pk=buddy_instance.pk)

    def test_create_old_to_new(self):
        """
        Asserts that an instance of the new model is created when
        a single instance of any of the old models is created
        """
        self.switch.active = False
        self.switch.save()
        for _, old_model_factory in self.old_models_descriptors_and_factories:
            self._create_and_assert_in_sync(
                old_model_factory,
                [self.new_model_descriptor],
            )

    def test_update_old_to_new(self):
        """
        Asserts model sync after an update to a single instance
        of the old model
        """
        self.switch.active = False
        self.switch.save()
        for old_model_descriptor, old_model_factory in \
                self.old_models_descriptors_and_factories:
            if not old_model_descriptor.get('read_only'):
                self._update_and_assert_in_sync(
                    old_model_descriptor,
                    old_model_factory,
                    [self.new_model_descriptor],
                    self.update_old_to_new_dict,
                )

    def test_update_old_to_new_without_existing_new(self):
        """
        Asserts model sync after a single instance of the old model
        where no related new model exists
        """
        self.switch.active = False
        self.switch.save()
        for old_model_descriptor, old_model_factory in \
                self.old_models_descriptors_and_factories:
            if not old_model_descriptor.get('read_only'):
                self._update_and_assert_in_sync(
                    old_model_descriptor,
                    old_model_factory,
                    [self.new_model_descriptor],
                    self.update_old_to_new_dict,
                    without_target_existing=True,
                )

    def test_delete_old_to_new(self):
        """
        Asserts model sync after a delete to a single instance
        of the old model
        """
        self.switch.active = False
        self.switch.save()
        for old_model_descriptor, old_model_factory in \
                self.old_models_descriptors_and_factories:
            if not old_model_descriptor.get('read_only'):
                self._delete_and_assert_in_sync(
                    old_model_descriptor,
                    old_model_factory,
                    [self.new_model_descriptor],
                )

    def test_delete_old_without_existing_new(self):
        """
        Asserts that deleting an old instance that doesn't have a new instance
        in sync does not raise an error
        """
        self.switch.active = False
        self.switch.save()
        for old_model_descriptor, old_model_factory in \
                self.old_models_descriptors_and_factories:
            self._delete_and_assert_in_sync(
                old_model_descriptor,
                old_model_factory,
                without_target_existing=True,
            )

    def test_create_new_to_old(self):
        """
        Since multiple old models can map to a single new model, we actually
        need just one assertion to pass in
        our calls to :function: `_create_and_assert_in_sync()` here
        """
        self.switch.active = True
        self.switch.save()
        old_model_descriptors = [
            old_model_descriptor for old_model_descriptor, _ in
            self.old_models_descriptors_and_factories]

        self._create_and_assert_in_sync(
            self.new_model_factory,
            old_model_descriptors,
        )

    def test_update_new_to_old(self):
        """
        Asserts model sync after an update to a single instance
        of the new model"""
        self.switch.active = True
        self.switch.save()
        old_models_descriptors = []
        for descriptor, _ in self.old_models_descriptors_and_factories:
            old_models_descriptors.append(descriptor)
        self._update_and_assert_in_sync(
            self.new_model_descriptor,
            self.new_model_factory,
            old_models_descriptors,
            self.update_new_to_old_dict,
        )

    def test_delete_new_to_old(self):
        """
        Asserts model sync after a delete to a single instance
        of the new model"""
        self.switch.active = True
        self.switch.save()
        old_model_descriptors = [
            old_model_descriptor for old_model_descriptor, _ in
            self.old_models_descriptors_and_factories]

        self._delete_and_assert_in_sync(
            self.new_model_descriptor,
            self.new_model_factory,
            old_model_descriptors,
        )

    def test_update_new_to_old_without_existing_old(self):
        """Asserts model sync after a single instance of the new model
        where no related old model exists"""
        self.switch.active = True
        self.switch.save()
        old_models_descriptors = []
        for descriptor, _ in self.old_models_descriptors_and_factories:
            old_models_descriptors.append(descriptor)
        if not self.new_model_descriptor.get('read_only'):
            self._update_and_assert_in_sync(
                self.new_model_descriptor,
                self.new_model_factory,
                old_models_descriptors,
                self.update_new_to_old_dict,
                without_target_existing=True
            )

    def test_delete_new_without_existing_old(self):
        """
        Asserts that deleting a new instance that doesn't have an old instance
        in sync does not raise an error
        """
        self.switch.active = True
        self.switch.save()

        self._delete_and_assert_in_sync(
            self.new_model_descriptor,
            self.new_model_factory,
            without_target_existing=True,
        )
