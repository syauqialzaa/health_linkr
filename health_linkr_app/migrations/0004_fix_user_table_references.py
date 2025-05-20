from django.db import migrations
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('health_linkr_app', '0003_alter_role_name'),
        ('admin', '0003_logentry_add_action_flag_choices'),
    ]

    operations = [
        migrations.RunSQL(
            # Forward SQL
            """
            DELETE FROM django_admin_log;
            ALTER TABLE django_admin_log DROP CONSTRAINT IF EXISTS django_admin_log_user_id_c564eba6_fk_auth_user_id;
            ALTER TABLE django_admin_log
                ADD CONSTRAINT django_admin_log_user_id_fk
                FOREIGN KEY (user_id)
                REFERENCES health_linkr_app_user(id)
                ON DELETE SET NULL;
            """,
            # Reverse SQL
            """
            DELETE FROM django_admin_log;
            ALTER TABLE django_admin_log DROP CONSTRAINT IF EXISTS django_admin_log_user_id_fk;
            ALTER TABLE django_admin_log
                ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id
                FOREIGN KEY (user_id)
                REFERENCES auth_user(id)
                ON DELETE SET NULL;
            """
        ),
    ]
