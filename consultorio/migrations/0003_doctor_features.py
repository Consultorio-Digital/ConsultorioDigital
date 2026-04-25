import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultorio', '0002_reserva_estado'),
    ]

    operations = [
        # Consultorio asignado al Profesional
        migrations.AddField(
            model_name='profesional',
            name='consultorio',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='profesionales',
                to='consultorio.consultorio',
            ),
        ),
        # Profesional que confirmó la Reserva
        migrations.AddField(
            model_name='reserva',
            name='profesional',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='reservas_confirmadas',
                to='consultorio.profesional',
            ),
        ),
        # Modelo Disponibilidad
        migrations.CreateModel(
            name='Disponibilidad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha',       models.DateField()),
                ('hora_inicio', models.TimeField()),
                ('hora_fin',    models.TimeField()),
                ('profesional', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='disponibilidades',
                    to='consultorio.profesional',
                )),
            ],
            options={
                'ordering': ['fecha', 'hora_inicio'],
            },
        ),
        migrations.AddConstraint(
            model_name='disponibilidad',
            constraint=models.UniqueConstraint(
                fields=['profesional', 'fecha', 'hora_inicio'],
                name='unique_disponibilidad',
            ),
        ),
    ]
