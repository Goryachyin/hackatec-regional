import uuid
from django.conf import settings
from django.db import models

AREAS = {'proteccion_civil': 'Protección Civil', 'obras_publicas': 'Obras Públicas', 'ecologia': 'Ecología'}
GENERAL = {'ine', 'curp', 'cfe'}
REQUIREMENTS = {
    'proteccion_civil': GENERAL | {'pc_pago', 'pc_uso_suelo'},
    'obras_publicas': GENERAL | {'op_solicitud', 'op_predial'},
    'ecologia': GENERAL | {'eco_recoleccion', 'eco_solicitud'},
}
KINDS = set.union(*REQUIREMENTS.values())


class Dossier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=80)
    folio = models.CharField(max_length=40)
    manifest = models.JSONField()
    ready = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class File(models.Model):
    id = models.UUIDField(primary_key=True)
    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name='files')
    kind = models.CharField(max_length=30)
    name = models.CharField(max_length=255)
    mime = models.CharField(max_length=60)
    digest = models.CharField(max_length=64)
    # Copias privadas en PostgreSQL para una demo acotada; no dependen del disco efímero.
    content = models.BinaryField()


class Reviewer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    area = models.CharField(max_length=30, choices=list(AREAS.items()))


class Decision(models.Model):
    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name='decisions')
    area = models.CharField(max_length=30, choices=list(AREAS.items()))
    outcome = models.CharField(max_length=10, choices=[('approved', 'Aprobada'), ('rejected', 'Rechazada')])
    notes = models.TextField(blank=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['dossier', 'area'], name='one_decision_per_area')]


class LoginAttempt(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    count = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField()
