from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultorio', '0006_reserva_notas_doctor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reserva',
            name='estado',
            field=models.CharField(
                choices=[
                    ('pendiente',   'Pendiente'),
                    ('confirmada',  'Confirmada'),
                    ('completada',  'Completada'),
                    ('seguimiento', 'Seguimiento'),
                    ('cancelada',   'Cancelada'),
                    ('no_asistio',  'No asistió'),
                ],
                default='pendiente',
                max_length=20,
            ),
        ),
    ]
