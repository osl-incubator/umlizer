"""Set of functions for integrating to django."""

import os


def setup(settings_module: str) -> None:
    """
    Set up the Django environment.

    Parameters
    ----------
    settings_module : str
        The Django settings module to use.
    """
    import django

    os.environ['DJANGO_SETTINGS_MODULE'] = settings_module
    django.setup()
