# flake8: noqa
import structlog as logging
from functools import wraps

logger = logging.getLogger(__name__)


def try_both_switch_settings(switch):
    def decorate_function(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Switch.objects.filter(
            #     organization=self.organization,
            #     feature=switch,
            # ).delete()
            #
            # logger.info(
            #     f'Running test function {func.__name__} without '
            #     f'feature switch')
            # func(self, *args, **kwargs)
            #
            # Switch.objects.create(
            #     organization=self.organization,
            #     feature=switch,
            #     active=True
            # )
            # logger.info(
            #     f'Running test function {func.__name__} WITH '
            #     f'feature switch')
            func(self, *args, **kwargs)
        return wrapper
    return decorate_function
