import frappe


def after_sync():
    """
    Runs at the end of `bench install-app`, after DocTypes and
    fixtures have been synced.

    Adopt existing Companies/Users into tenants and add the
    tenant/company fields to shared doctypes. Both steps are
    idempotent, so re-running install or migrate is safe.
    """

    from songa_multi_tenancy.patches.v1.adoption.adopt_existing_companies import (
        execute as adopt_existing_companies,
    )
    from songa_multi_tenancy.patches.v1.custom_fields.add_custom_fields import (
        execute as add_custom_fields,
    )

    adopt_existing_companies()
    add_custom_fields()
