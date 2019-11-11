import typing as t
import structlog as logging

logger = logging.getLogger(__name__)


def call_with_error_handling_if_condition(
        func: t.Callable,
        handle_errors: bool,
        *args,
        **kwargs) -> bool:
    """
    Utility function to call passed `func`. If `wrap_call` is True, func
    execution is wrapped in `call_with_error_handling`

    *args, **kwargs are passed to `func`

    Returns function result
    """

    if handle_errors:
        return call_with_error_handling(func, *args, **kwargs)
    return func(*args, **kwargs)


def call_with_error_handling(func: t.Callable, *args, **kwargs) -> bool:
    """
    Utility function, wraps `func` invocation in `try..except Exception`
    block to catch everything and log in this case.

    *args, **kwargs are passed to `func`

    Returns function result in case of success, and False otherwise
    """

    try:
        return func(*args, **kwargs)
    except Exception as exc:
        logger.error(
            f'Error while calling {func.__name__}: {exc}',
            exc_info=True,
            stack_info=True)
        return False


class AutoSynchronizationBase:
    def delete(self, *args, **kwargs):
        logger.debug(f'AUTO-SYNC: Starting delete for instance: {self} of '
                     f'class: {self.__class__.__name__}. ')

        target = kwargs.pop('target', False)
        is_synching_old_to_new = kwargs.pop('is_synching_old_to_new', False)

        call_post_delete = call_with_error_handling_if_condition(
            func=self._pre_delete,
            handle_errors=is_synching_old_to_new,
            target=target,
            *args,
            **kwargs)

        super().delete(*args, **kwargs)

        if call_post_delete:
            call_with_error_handling_if_condition(
                func=self._post_delete,
                handle_errors=is_synching_old_to_new,
                target=target,
                *args,
                **kwargs
            )

        logger.debug(f'AUTO-SYNC: Completed delete for instance: {self} of'
                     f' class: {self.__class__.__name__}. ')

    def _pre_delete(self, *args, target: bool, **kwargs) -> bool:
        raise NotImplementedError(
            'AutoSynchronizationBase requires the function _pre_delete() '
            'to be implemented')

    def _post_delete(self, *args, target: bool, **kwargs) -> None:
        raise NotImplementedError(
            'AutoSynchronizationBase requires the function _post_delete()'
            ' to be implemented')

    def save(self, *args, **kwargs):
        logger.debug(
            f'AUTO-SYNC: Starting save for instance: {self} of class:'
            f' {self.__class__.__name__}. ')
        if hasattr(self, 'exists_in_db'):
            update = self.exists_in_db()
        else:
            update = bool(self.pk)

        logger.debug(f'AUTO-SYNC: Update: {update}')

        target = kwargs.pop('target', False)
        is_synching_old_to_new = kwargs.pop('is_synching_old_to_new', False)

        call_post_save = call_with_error_handling_if_condition(
            func=self._pre_save,
            handle_errors=is_synching_old_to_new,
            update=update,
            target=target,
            *args,
            **kwargs
        )

        super().save(*args, **kwargs)

        if call_post_save:
            call_with_error_handling_if_condition(
                func=self._post_save,
                handle_errors=is_synching_old_to_new,
                update=update,
                target=target,
                *args,
                **kwargs
            )

        logger.debug(
            f'AUTO-SYNC: Completed save for instance: {self} of class:'
            f' {self.__class__.__name__}. ')

    def _pre_save(self, *args, update: bool, target: bool, **kwargs) -> bool:
        raise NotImplementedError(
            'AutoSynchronizationBase requires the function _pre_save() '
            'to be implemented')

    def _post_save(self, *args, update: bool, target: bool, **kwargs) -> None:
        raise NotImplementedError(
            'AutoSynchronizationBase requires the function _post_save() '
            'to be implemented')
