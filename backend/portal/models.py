import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    email = models.EmailField(unique=True)
    curp = models.CharField(max_length=18, unique=True)
    email_verified = models.BooleanField(default=False)


class Verification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    sent_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)


class AuthAttempt(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    window_start = models.DateTimeField()
    count = models.PositiveIntegerField(default=0)


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    procedure = models.CharField(max_length=40)
    reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, default='draft')
    folio = models.CharField(max_length=40, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True)


def document_path(instance, filename):
    return f'{instance.owner_id}/{uuid.uuid4().hex}'


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kind = models.CharField(max_length=30)
    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to=document_path)
    content_type = models.CharField(max_length=60)
    size = models.PositiveIntegerField()
    in_vault = models.BooleanField(default=False)
    temporary_for = models.ForeignKey(Application, null=True, blank=True, on_delete=models.CASCADE, related_name='temporary_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    analysis_status = models.CharField(max_length=20, default='not_analyzed')
    analysis_result = models.JSONField(default=dict, blank=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)


class Attachment(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='attachments')
    document = models.ForeignKey(Document, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['application', 'document'], name='unique_attachment')]
