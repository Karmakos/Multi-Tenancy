import frappe

# Modules whose DocTypes are automatically tenant/company scoped.
SCOPED_MODULES = [
    "Songa App Integration",
    "Songa Custom",
    "Boya Integration",
    "Stanbic",
    "Frappe Mpsa Payments",
    "Payments Processor",
    "Payments"
]


def get_tenant_scoped_doctypes():
    """DocTypes that receive tenant/company scoping.

    Combines the explicitly listed shared/master DocTypes with every
    non-Single, non-child-table DocType under SCOPED_MODULES, so new
    DocTypes added to those modules are picked up automatically.
    """

    doctypes = [
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
        "Lead",
    ]

    module_doctypes = frappe.get_all(
        "DocType",
        filters={
            "module": ["in", SCOPED_MODULES],
            "istable": 0,
            "issingle": 0,
        },
        pluck="name",
    )

    return list(dict.fromkeys(doctypes + module_doctypes))
