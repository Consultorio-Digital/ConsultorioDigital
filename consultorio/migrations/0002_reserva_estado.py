from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultorio', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='estado',
            field=models.CharField(
                choices=[
                    ('pendiente',  'Pendiente'),
                    ('confirmada', 'Confirmada'),
                    ('cancelada',  'Cancelada'),
                ],
                default='pendiente',
                max_length=20,
            ),
        ),
    ]
