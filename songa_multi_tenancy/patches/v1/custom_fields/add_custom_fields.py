


from songa_multi_tenancy.patches.v1.custom_fields.update_tenants_and_company import update_tenant_and_company_fields
from songa_multi_tenancy.patches.v1.custom_fields.add_tenant_and_company_fields import add_tenant_and_company_fields


def execute():
    add_tenant_and_company_fields()
    update_tenant_and_company_fields()
    