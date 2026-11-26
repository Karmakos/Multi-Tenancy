import frappe

LOGGER = frappe.logger("songa_multi_tenancy")


def get_existing_companies():
    """Return all Companies ordered oldest first."""

    return frappe.get_all(
        "Company",
        fields=["name", "company_name", "creation"],
        order_by="creation asc, name asc",
    )


def skip_adoption():
    """Log that no Company exists and adoption was skipped."""

    LOGGER.info(
        "Installation adoption skipped: no Company exists. "
        "No Tenant, Tenant User, or administrator records were created."
    )

def require_doctype(doctype):
    if not frappe.db.exists("DocType", doctype):
        frappe.throw(
            f"Required DocType '{doctype}' does not exist. "
            "Ensure the DocType is installed before running this patch."
        )





def has_field(doctype, fieldname):
    return frappe.get_meta(doctype).has_field(fieldname)


def set_if_field_exists(doc, fieldname, value):
    if doc.meta.has_field(fieldname):
        doc.set(fieldname, value)
        return True
    return False


def set_first_available_field(doc, fieldnames, value):
    for fieldname in fieldnames:
        if doc.meta.has_field(fieldname):
            doc.set(fieldname, value)
            return fieldname
    return None


def set_select_if_valid(doc, fieldname, value):
    """Set a Select field only when the value is among its configured options."""

    if not doc.meta.has_field(fieldname):
        return False

    df = doc.meta.get_field(fieldname)

    options = [
        option.strip()
        for option in (df.options or "").splitlines()
        if option.strip()
    ]

    if options and value not in options:
        return False

    doc.set(fieldname, value)
    return True


 # Activate tenants only after every step succeeds.
def update_tenant_status(tenants):
        for tenant in tenants.values():
            tenant_name = (
                tenant.name
                if hasattr(tenant, "name")
                else tenant
            )

            frappe.db.set_value(
                "Tenant",
                tenant_name,
                "status",
                "Active",
            )