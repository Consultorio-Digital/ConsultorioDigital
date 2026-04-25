from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultorio', '0004_reserva_seguimiento'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='motivo_cancelacion',
            field=models.CharField(max_length=500, null=True, blank=True),
        ),
    ]
