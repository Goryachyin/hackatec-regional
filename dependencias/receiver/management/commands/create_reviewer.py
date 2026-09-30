from getpass import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from receiver.models import AREAS, Reviewer


class Command(BaseCommand):
    help = 'Crea un revisor limitado a un área; solicita contraseña sin mostrarla.'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('area', choices=list(AREAS))

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(username=options['username']).exists():
            raise CommandError('El usuario ya existe.')
        password = getpass('Contraseña (mínimo 12 caracteres): ')
        if len(password) < 12 or password != getpass('Repite la contraseña: '):
            raise CommandError('Las contraseñas deben coincidir y tener al menos 12 caracteres.')
        user = User(username=options['username'])
        try:
            validate_password(password, user)
        except ValidationError as exc:
            raise CommandError(' '.join(exc.messages)) from exc
        from django.db import transaction
        with transaction.atomic():
            user.set_password(password)
            user.save()
            Reviewer.objects.create(user=user, area=options['area'])
        self.stdout.write(self.style.SUCCESS('Revisor creado.'))
