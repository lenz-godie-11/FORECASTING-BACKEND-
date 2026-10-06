from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from src.auth.roles import ADMIN, MANAGER


class Command(BaseCommand):
    help = "Create or update a staff account with an ADMIN or MANAGER role."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument(
            "password",
            nargs="?",
            default=None,
            help="Password for the account. Omit to generate one.",
        )
        parser.add_argument(
            "--role",
            choices=[ADMIN, MANAGER],
            default=MANAGER,
            help="Role to assign (default: MANAGER).",
        )

    def handle(self, *args, **options):
        username = options["username"]
        role = options["role"]
        password = options["password"]

        user, created = User.objects.get_or_create(username=username)

        if password:
            user.set_password(password)
        elif created:
            password = get_random_string(length=16)
            user.set_password(password)

        user.is_active = True
        user.save()

        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(f"{action} staff account '{username}' (role={role}).")
        )

        if created and not options["password"]:
            self.stdout.write(f"Generated password: {password}")
