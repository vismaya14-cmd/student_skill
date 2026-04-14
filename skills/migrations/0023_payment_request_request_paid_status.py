from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('skills', '0022_alter_notification_options_alter_payment_options_and_more'),
    ]

    operations = [
        # Add 'paid' to Request.status choices
        migrations.AlterField(
            model_name='request',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('accepted', 'Accepted'),
                    ('rejected', 'Rejected'),
                    ('completed', 'Completed'),
                    ('paid', 'Paid'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
        # Add request FK to Payment model (OneToOne, nullable for legacy payments)
        migrations.AddField(
            model_name='payment',
            name='request',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='request_payment',
                to='skills.request',
            ),
        ),
    ]
