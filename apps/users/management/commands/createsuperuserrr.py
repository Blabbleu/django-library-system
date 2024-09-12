from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.management import CommandError
from apps.users.models import CustomUser

class Command(BaseCommand):
    help = 'Create a superuser along with StaffProfile fields'

    def handle(self, *args, **kwargs):
        username = input('Username: ')
        email = input('Email: ')
        password = input('Password: ')
        date_of_birth = input('Date of Birth (YYYY-MM-DD): ')
        address = input('Address: ')
        phone_number = input('Phone Number: ')
        level_of_education = input('Level of Education (HS/IN/AD/BA/MA/PH): ')
        department = input('Department (LI/WK/TR/BD): ')
        position = input('Position (DI/DD/DH/DDH/SM): ')

        if not username or not email or not password:
            raise CommandError("Username, email, and password are required")

        user = User.objects.create_superuser(username=username, email=email, password=password)
        CustomUser.objects.create(
            user=user,
            date_of_birth=date_of_birth,
            address=address,
            phone_number=phone_number,
            level_of_education=level_of_education,
            department=department,
            position=position
        )
        self.stdout.write(self.style.SUCCESS('Successfully created superuser and staff profile'))

