from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile

class Command(BaseCommand):
    help = 'Makes a user an instructor'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user to make instructor')

    def handle(self, *args, **options):
        username = options['username']
        try:
            user = User.objects.get(username=username)
            profile = user.userprofile
            profile.user_type = 'instructor'
            profile.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully made {username} an instructor'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} does not exist')) 