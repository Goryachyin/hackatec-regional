from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('portal', '0002_document_analysis')]
    operations = [
        migrations.AddField(model_name='user', name='can_simulate_documents', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='document', name='is_simulated', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='application', name='is_demo', field=models.BooleanField(default=False)),
    ]
