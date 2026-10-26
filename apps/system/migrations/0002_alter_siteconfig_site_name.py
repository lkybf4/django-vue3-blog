from django.db import migrations, models


PLACEHOLDER_NAMES = ['TendCode', 'self-blog', '我的博客', '']


def rename_placeholder_site(apps, schema_editor):
    """把旧默认名/占位名升级为新品牌名，用户自定义过的名称保持不变。"""
    SiteConfig = apps.get_model('system', 'SiteConfig')
    SiteConfig.objects.filter(site_name__in=PLACEHOLDER_NAMES).update(
        site_name='文栈 Wenstack'
    )


class Migration(migrations.Migration):
    dependencies = [
        ('system', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteconfig',
            name='site_name',
            field=models.CharField(
                default='文栈 Wenstack', max_length=100, verbose_name='站点名称'
            ),
        ),
        migrations.RunPython(rename_placeholder_site, migrations.RunPython.noop),
    ]
