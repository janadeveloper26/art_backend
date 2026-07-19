from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_video_file'),
    ]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: schema_editor.connection.cursor().execute("""
                DO $$ DECLARE
                    _conname text;
                BEGIN
                    SELECT conname INTO _conname FROM pg_constraint
                    WHERE conrelid = 'courses'::regclass
                      AND contype = 'f'
                      AND conname LIKE '%instructor_id%'
                    LIMIT 1;
                    IF FOUND THEN
                        EXECUTE 'ALTER TABLE courses DROP CONSTRAINT ' || _conname;
                    END IF;
                END $$;
                UPDATE courses SET instructor_id = NULL
                WHERE instructor_id IS NOT NULL
                  AND length(trim(instructor_id::text)) > 15;
                DROP INDEX IF EXISTS courses_instructor_id_801fc5d2;
                ALTER TABLE courses ALTER COLUMN instructor_id TYPE bigint
                    USING (nullif(btrim(instructor_id::text), ''))::bigint;
                ALTER TABLE courses ADD CONSTRAINT courses_instructor_id_fkey
                    FOREIGN KEY (instructor_id) REFERENCES accounts_user(id)
                    ON DELETE SET NULL;
            """) if schema_editor.connection.vendor == 'postgresql' else None,
            reverse_code=lambda apps, schema_editor: schema_editor.connection.cursor().execute("""
                ALTER TABLE courses DROP CONSTRAINT IF EXISTS courses_instructor_id_fkey;
                ALTER TABLE courses ALTER COLUMN instructor_id TYPE uuid
                    USING gen_random_uuid();
            """) if schema_editor.connection.vendor == 'postgresql' else None,
        ),
    ]
