from django.test.runner import DiscoverRunner


class ManagedModelTestRunner(DiscoverRunner):

    def setup_databases(self, **kwargs):
        from django.apps import apps
        for m in apps.get_models():
            try:
                m._meta.read_db = m._meta.write_db
                if m._meta.read_db == 'pg_master':
                    m._meta.managed = True
            except AttributeError:
                m._meta.read_db = m._meta.write_db = 'default'

        return super(ManagedModelTestRunner, self).setup_databases(**kwargs)

    def teardown_test_environment(self, **kwargs):
        super(ManagedModelTestRunner, self).teardown_test_environment(**kwargs)


