from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Start face recognition attendance camera'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting FaceTrack face recognition...'))
        try:
            from attendance.face_utils import run_face_recognition_camera
            run_face_recognition_camera()
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Missing libraries: {e}'))
            self.stdout.write('Install: pip install opencv-python face-recognition')
