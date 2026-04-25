from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultorio', '0005_reserva_motivo_cancelacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='notas_doctor',
            field=models.TextField(null=True, blank=True),
        ),
    ]
