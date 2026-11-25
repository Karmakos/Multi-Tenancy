import frappe

# DocTypes that receive tenant/company Custom Fields from
# patches/v1/custom_fields/add_tenant_and_company_fields.py
SCOPED_DOCTYPES = [
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
    "Driver",
    "Songa Webhook Log",
    "Mpesa Express Request",
    "Lead",
]

# fieldname -> expected Link target
SCOPED_FIELDS = {
    "tenant": "Tenant",
    "company": "Company",
}


def after_uninstall():
    """
    Remove the Custom Fields this app added to core DocTypes.

    The app's own DocTypes are dropped automatically on uninstall;
    this only cleans up the tenant/company columns left behind on
    shared doctypes. A field is only removed when it is a Link to
    the expected target, so unrelated custom fields are kept.
    """

    removed = 0

    for doctype in SCOPED_DOCTYPES:
        for fieldname, link_target in SCOPED_FIELDS.items():
            custom_field = frappe.db.get_value(
                "Custom Field",
                {"dt": doctype, "fieldname": fieldname},
                ["name", "fieldtype", "options"],
                as_dict=True,
            )

            if not custom_field:
                continue

            if (
                custom_field.fieldtype != "Link"
                or custom_field.options != link_target
            ):
                continue

            frappe.delete_doc(
                "Custom Field",
                custom_field.name,
                ignore_permissions=True,
                force=True,
            )
            removed += 1

    frappe.db.commit()

    frappe.logger("songa_multi_tenancy").info(
        "Removed %s tenant/company Custom Fields.", removed
    )
