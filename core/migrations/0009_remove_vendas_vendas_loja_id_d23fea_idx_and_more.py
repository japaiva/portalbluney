# Generated by Django 5.1.7 on 2025-06-08 18:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_remove_vendas_vendas_loja_id_e3f370_idx_and_more'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='vendas',
            name='vendas_loja_id_d23fea_idx',
        ),
        migrations.RemoveIndex(
            model_name='vendas',
            name='vendas_vendedo_a35297_idx',
        ),
        migrations.AddField(
            model_name='vendas',
            name='vendedor',
            field=models.ForeignKey(default=999, on_delete=django.db.models.deletion.PROTECT, to='core.vendedor', verbose_name='Vendedor'),
            preserve_default=False,
        ),
        migrations.AddIndex(
            model_name='vendas',
            index=models.Index(fields=['loja', 'vendedor', 'produto'], name='vendas_loja_id_e3f370_idx'),
        ),
    ]
