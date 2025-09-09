from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0006_remove_materialsupplier_lead_time_days"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE "catalog_material"
                  ALTER COLUMN "stock" SET DEFAULT 0;
                UPDATE "catalog_material"
                  SET "stock" = 0
                  WHERE "stock" IS NULL;
                ALTER TABLE "catalog_material"
                  ALTER COLUMN "stock" SET NOT NULL;
            """,
            reverse_sql="""
                -- Reversa opcional: quita el NOT NULL y el DEFAULT
                ALTER TABLE "catalog_material"
                  ALTER COLUMN "stock" DROP NOT NULL;
                ALTER TABLE "catalog_material"
                  ALTER COLUMN "stock" DROP DEFAULT;
            """,
        ),
    ]
