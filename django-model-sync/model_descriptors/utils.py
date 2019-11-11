"""
Utility classes for model descriptors, meant to package commonly performed
commands into small functions
"""
from django.apps import apps


def get_model_class(descriptor):
    """
    Get model class
    :param descriptor: model descriptor
    :return:
    """
    app_name = descriptor['app_name']
    model_name = descriptor['model_name']
    return apps.get_model(app_name, model_name)


def get_buddy_class(descriptor):
    """
    Get buddy class
    :param descriptor: model descriptor
    :return:
    """
    buddy_app_name = descriptor['buddy_app_name']
    buddy_model_name = descriptor['buddy_model_name']
    return apps.get_model(buddy_app_name, buddy_model_name)
