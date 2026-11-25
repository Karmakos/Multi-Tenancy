import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from songa_multi_tenancy.patches.v1.custom_fields.scoped_doctypes import (
    get_tenant_scoped_doctypes,
)


def add_tenant_and_company_fields():
    # Shared/master DocTypes plus every DocType under SCOPED_MODULES
    tenant_scoped_doctypes = get_tenant_scoped_doctypes()

    custom_fields = {}

    for doctype in tenant_scoped_doctypes:
        meta = frappe.get_meta(doctype)
        fields_to_add = []

        # 1. Add 'tenant' Link field if it doesn't already exist
        if not meta.has_field("tenant"):
            fields_to_add.append({
                "fieldname": "tenant",
                "label": "Tenant",
                "fieldtype": "Link",
                "options": "Tenant",
                "insert_after": "naming_series" if meta.has_field("naming_series") else "",
                "in_standard_filter": 1,
                "search_index": 1,  # Essential for performance with permission queries
                "read_only": 1,
            })

        # 2. Add 'company' Link field if the DocType lacks a standard company field
        if not meta.has_field("company"):
            fields_to_add.append({
                "fieldname": "company",
                "label": "Company",
                "fieldtype": "Link",
                "options": "Company",
                "insert_after": "tenant",
                "in_standard_filter": 1,
                "search_index": 1,
                "read_only": 1,
            })

        if fields_to_add:
            custom_fields[doctype] = fields_to_add

    if custom_fields:
        # Create or update the custom fields safely across the site
        create_custom_fields(custom_fields, update=True)
        frappe.db.commit()