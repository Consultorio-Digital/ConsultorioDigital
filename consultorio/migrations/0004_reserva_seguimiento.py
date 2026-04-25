from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultorio', '0003_doctor_features'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='fecha_seguimiento',
            field=models.DateField(blank=True, null=True),
        ),
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
                ],
                default='pendiente',
                max_length=20,
            ),
        ),
    ]
