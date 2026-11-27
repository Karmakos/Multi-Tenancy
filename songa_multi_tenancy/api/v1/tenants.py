import frappe
from frappe import _

from songa_multi_tenancy.permissions import get_user_tenant, is_platform_admin


@frappe.whitelist()
def current_tenant():
    """Return the session user's active tenant docname (or None)."""

    return get_user_tenant() or ""


def _require_platform_admin():
    if not is_platform_admin():
        frappe.throw(_("Not permitted."), frappe.PermissionError)


@frappe.whitelist(methods=["POST"])
def suspend_tenant(tenant):
    """Suspend a tenant: disables its Tenant User memberships."""

    _require_platform_admin()

    doc = frappe.get_doc("Tenant", tenant)
    doc.suspend()

    return {
        "tenant": doc.name,
        "company": doc.company,
        "status": doc.status,
    }


@frappe.whitelist(methods=["POST"])
def pause_tenant(tenant):
    """Pause a tenant: disables its Tenant User memberships."""

    _require_platform_admin()

    doc = frappe.get_doc("Tenant", tenant)
    doc.pause()

    return {
        "tenant": doc.name,
        "company": doc.company,
        "status": doc.status,
    }


@frappe.whitelist(methods=["POST"])
def activate_tenant(tenant):
    """Reactivate a suspended tenant and its memberships."""

    _require_platform_admin()

    doc = frappe.get_doc("Tenant", tenant)
    doc.activate()

    return {
        "tenant": doc.name,
        "company": doc.company,
        "status": doc.status,
    }


@frappe.whitelist(methods=["POST"])
def archive_tenant(tenant):
    """Archive a tenant: disables memberships and member logins.
    Data is preserved and the tenant can be reactivated."""

    _require_platform_admin()

    doc = frappe.get_doc("Tenant", tenant)
    doc.archive()

    return {
        "tenant": doc.name,
        "company": doc.company,
        "status": doc.status,
    }


@frappe.whitelist(methods=["POST"])
def delete_tenant(tenant):
    """Soft-delete a tenant: status becomes Deleted and all member
    Users are disabled so they cannot log in. Data is preserved."""

    _require_platform_admin()

    doc = frappe.get_doc("Tenant", tenant)
    doc.mark_deleted()

    return {
        "tenant": doc.name,
        "company": doc.company,
        "status": doc.status,
    }
