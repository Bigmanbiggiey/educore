from types import SimpleNamespace

from apps.core.context import bind_institution
from apps.core.db_router import TenantDBRouter


def test_shared_row_tenant_routes_to_default():
    router = TenantDBRouter()
    institution = SimpleNamespace(isolation_tier="shared_row", db_alias="")
    with bind_institution(institution):
        assert router.db_for_read(None) == "default"
        assert router.db_for_write(None) == "default"


def test_dedicated_db_tenant_routes_to_its_alias():
    router = TenantDBRouter()
    institution = SimpleNamespace(isolation_tier="dedicated_db", db_alias="st_mary_db")
    with bind_institution(institution):
        assert router.db_for_read(None) == "st_mary_db"


def test_no_bound_tenant_routes_to_default():
    router = TenantDBRouter()
    assert router.db_for_read(None) == "default"


def test_platform_apps_only_migrate_to_default():
    router = TenantDBRouter()
    assert router.allow_migrate("default", "institutions") is True
    assert router.allow_migrate("st_mary_db", "institutions") is False
    assert router.allow_migrate("default", "core") is True
    assert router.allow_migrate("st_mary_db", "core") is False


def test_tenant_apps_migrate_everywhere():
    router = TenantDBRouter()
    assert router.allow_migrate("default", "students") is True
    assert router.allow_migrate("st_mary_db", "students") is True
