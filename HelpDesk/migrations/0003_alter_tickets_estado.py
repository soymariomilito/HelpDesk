# Generated by Django 5.1.3 on 2024-11-09 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HelpDesk', '0002_rename_ticket_tickets'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tickets',
            name='estado',
            field=models.CharField(choices=[('AB', 'Abierto'), ('EN', 'En atención'), ('ES', 'Esperando 3ro'), ('DU', 'Duplicado'), ('RE', 'Resuelto'), ('CE', 'Cerrado')], default='AB', max_length=2),
        ),
    ]