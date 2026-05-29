from django.db import migrations, models
import django.db.models.deletion
import pgvector.django

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('location', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('experience_level', models.CharField(choices=[('intern', 'Intern'), ('entry', 'Entry Level'), ('senior', 'Senior Level')], max_length=30, null=True)),
                ('work_mode', models.CharField(max_length=20, null=True)),
                ('job_type', models.CharField(max_length=20, null=True)),
                ('salary', models.CharField(max_length=50, null=True)),
                ('employer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jobs', to='auth.user')),
            ],
        ),
        migrations.CreateModel(
            name='JobChunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section', models.CharField(default='general', max_length=100)),
                ('chunk_text', models.TextField()),
                ('embedding', pgvector.django.VectorField(dimensions=3072, null=True)),
                ('metadata', models.JSONField(default=dict)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='jobs.job')),
            ],
        ),
    ]