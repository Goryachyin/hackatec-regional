from django.db import migrations, models


def map_legacy(apps, schema_editor):
    # No convertir un antiguo comprobante genérico en CFE validado.
    # Se asigna la categoría esperada y se exige nuevo análisis antes de usarlo.
    apps.get_model('portal', 'Document').objects.filter(kind='domicilio').update(kind='cfe')


class Migration(migrations.Migration):
    dependencies = [('portal', '0001_initial')]
    operations = [
        migrations.AddField(model_name='document', name='analysis_status', field=models.CharField(default='not_analyzed', max_length=20)),
        migrations.AddField(model_name='document', name='analysis_result', field=models.JSONField(default=dict, blank=True)),
        migrations.AddField(model_name='document', name='analyzed_at', field=models.DateTimeField(null=True, blank=True)),
        migrations.RunPython(map_legacy, migrations.RunPython.noop),
    ]
