from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from attendance.models import UserRole


class Command(BaseCommand):
    help = 'Create the admin user for FaceTrack'

    def handle(self, *args, **options):
        if User.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING('Admin user already exists.'))
            return
        
        user = User.objects.create_superuser(
            username='admin',
            email='admin@facetrack.com',
            password='admin123',
            first_name='System',
            last_name='Admin',
        )
        UserRole.objects.create(user=user, role='admin')
        
        self.stdout.write(self.style.SUCCESS('Admin user created! Username: admin | Password: admin123'))
