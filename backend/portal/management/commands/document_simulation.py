from django.core.management.base import BaseCommand, CommandError
from portal.models import User


class Command(BaseCommand):
    help = 'Autoriza o revoca simulación documental para una cuenta existente, sin elevar privilegios.'

    def add_arguments(self, parser):
        parser.add_argument('email')
        parser.add_argument('--enable', action='store_true', help='Sin esta opción se revoca el permiso.')

    def handle(self, *args, **options):
        user = User.objects.filter(email__iexact=options['email']).first()
        if not user:
            raise CommandError('No existe una cuenta con ese correo.')
        user.can_simulate_documents = options['enable']
        user.save(update_fields=['can_simulate_documents'])
        self.stdout.write(self.style.SUCCESS('Permiso habilitado.' if options['enable'] else 'Permiso revocado.'))
