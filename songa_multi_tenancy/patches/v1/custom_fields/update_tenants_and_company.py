import frappe


SYSTEM_TENANT_TYPE = "System"


def update_tenant_and_company_fields():
    """
    Adopt existing shared-resource records under the SYSTEM tenant.

    - Finds the SYSTEM Tenant and its Company.
    - Assigns unassigned records to SYSTEM.
    - Assigns the SYSTEM Company.
    - Preserves records already assigned to another tenant.
    """

    tenant_scoped_doctypes = [
        "Item",
        "Item Group",
        "Brand",
        "Customer",
        "Customer Group",
        "Supplier",
        "Supplier Group",
        "Territory",
        "Price List",
        "Item Price",
        "Pricing Rule",
        "Holiday List",
        "Department",
        "Designation",
        "Branch",
        "Letter Head",
    ]

    # Get all tenants and identify SYSTEM

    tenants = frappe.get_all(
        "Tenant",
        fields=["name", "tenant_type", "company"],
    )

    system_tenants = [
        tenant for tenant in tenants
        if tenant.tenant_type == SYSTEM_TENANT_TYPE
    ]

    if len(system_tenants) != 1:
        frappe.throw(
            f"Expected exactly one SYSTEM Tenant, "
            f"found {len(system_tenants)}."
        )

    system_tenant = system_tenants[0]

    if not system_tenant.company:
        frappe.throw(
            "SYSTEM Tenant does not have an associated Company."
        )

    tenant_name = system_tenant.name
    company_name = system_tenant.company

    frappe.logger("songa_multi_tenancy").info(
        f"Adopting shared resources under "
        f"SYSTEM Tenant: {tenant_name}, Company: {company_name}"
    )

    # Update each DocType

    results = {}

    for doctype in tenant_scoped_doctypes:

        # Skip DocTypes not installed on this site.
        if not frappe.db.exists("DocType", doctype):
            results[doctype] = "Skipped: DocType not installed"
            continue

        meta = frappe.get_meta(doctype)

        has_tenant = meta.has_field("tenant")
        has_company = meta.has_field("company")

        if not has_tenant:
            results[doctype] = "Skipped: Missing tenant field"
            continue

        table = f"`tab{doctype}`"

        # Assign unowned records to SYSTEM.
        # Both fields are assigned together where available.
        if has_company:
            frappe.db.sql(
                f"""
                UPDATE {table}
                SET
                    tenant = %s,
                    company = %s
                WHERE
                    tenant IS NULL
                    OR tenant = ''
                """,
                (tenant_name, company_name),
            )
        else:
            frappe.db.sql(
                f"""
                UPDATE {table}
                SET tenant = %s
                WHERE
                    tenant IS NULL
                    OR tenant = ''
                """,
                (tenant_name,),
            )

        # Fill missing company only on records already belonging
        # to SYSTEM. Never overwrite another tenant's company.
        if has_company:
            frappe.db.sql(
                f"""
                UPDATE {table}
                SET company = %s
                WHERE
                    tenant = %s
                    AND (
                        company IS NULL
                        OR company = ''
                    )
                """,
                (company_name, tenant_name),
            )

        results[doctype] = "Updated"

    # Log results

    for doctype, result in results.items():
        frappe.logger("songa_multi_tenancy").info(
            f"{doctype}: {result}"
        )

    frappe.logger("songa_multi_tenancy").info(
        "SYSTEM tenant resource adoption completed."
    )

    return results