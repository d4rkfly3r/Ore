#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ore.settings.development")
    sys.path.append(os.getcwd())
    sys.path.append(os.path.join(os.getcwd(), 'ore'))

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
