
from os import name

import frappe
from frappe import _
from frappe.utils import now_datetime

from songa_multi_tenancy.api.v1.utils import reset_administrator_password


def api_response(success, message, status_code, data=None):
    """Standard response envelope."""

    return {
        "Success": success,
        "Message": message,
        "Status_code": status_code,
        "Data": data or {},
    }


@frappe.whitelist(methods=["POST"])
def register_tenant():
    """
    Accept a tenant registration request and enqueue provisioning.
    """

    try:
        payload = frappe.parse_json(frappe.request.get_json())

        songa_tenant_id = payload.get("Songa_tenant_id")
        company_name = payload.get("company")
        tenant_category = payload.get("tenant_category")
        admin = payload.get("admin") or {}

        email = (admin.get("email") or "").strip().lower()
        phone = admin.get("phone")
        full_name = (admin.get("full_name") or "").strip()

        # Validate required fields.
        if not all([
            songa_tenant_id,
            company_name,
            tenant_category,
            email,
            phone,
            full_name,
        ]):
            frappe.throw(
                _("Missing required tenant registration fields.")
            )

        if frappe.db.exists(
            "Tenant",
            {"songa_tenant_id": songa_tenant_id},
        ):
            frappe.throw(
                _("This Songa Tenant ID is already registered.")
            )

        existing_provision = frappe.db.get_value(
            "Tenant Provisioning",
            {"songa_tenant_id": songa_tenant_id},
            ["name", "provisioning_id", "status"],
            as_dict=True,
        )

        # Idempotency, no another provisioning request.
        if existing_provision:
            return api_response(
                True,
                "A provisioning request already exists.",
                409,
                {
                    "Songa_tenant_id": songa_tenant_id,
                    "provisioning_id": existing_provision.provisioning_id,
                    "status": existing_provision.status,
                },
            )

        if frappe.db.exists("User", email):
            frappe.throw(
                _("The administrator email is already registered.")
            )

        provisioning_id = frappe.generate_hash(length=20)

        provision = frappe.new_doc("Tenant Provisioning")
        provision.songa_tenant_id = songa_tenant_id
        provision.provisioning_id = provisioning_id
        provision.tenant_category = tenant_category
        provision.status = "Queued"
        provision.started_on = now_datetime()
        provision.payload = payload

        steps = [
            "Create Company",
            "Create Administrator User",
            "Assign Company Administrator Role",
            "Apply Company User Permission",
            "Create Tenant",
            "Activate Tenant",
        ]

        for sequence, step_name in enumerate(steps, start=1):
            provision.append(
                "progress",
                {
                    "step_name": step_name,
                    "sequence": sequence,
                },
            )

        provision.insert(ignore_permissions=True)


        frappe.enqueue(
            "songa_multi_tenancy.api.v1.provisioning.process_tenant_provisioning",
            queue="long",
            timeout=3600,
            enqueue_after_commit=True,
            provisioning_name=provision.name,
            company_name=company_name,
            admin_email=email,
            admin_phone=phone,
            admin_full_name=full_name,
        )

        # The request must be committed before the worker starts.
        frappe.db.commit()

        return api_response(
            True,
            "Tenancy Provisioning Queued successfully",
            202,
            {
                "Songa_tenant_id": songa_tenant_id,
                "provisioning_id": provisioning_id,
                "status": "Queued",
            },
        )

    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            frappe.get_traceback(),
            "Tenant Registration API Error",
        )
        raise


@frappe.whitelist(methods=["GET"])
def get_tenant_provisioning_status(
    Songa_tenant_id,
    provisioning_id,
):
    """Return the current state of a tenant provisioning request."""

    provision = frappe.db.get_value(
        "Tenant Provisioning",
        {
            "songa_tenant_id": Songa_tenant_id,
            "provisioning_id": provisioning_id,
        },
        ["name", "status", "tenant"],
        as_dict=True,
    )

    if not provision:
        frappe.local.response["http_status_code"] = 404
        return api_response(
            False,
            "Provisioning Request Not Found.",
            404,
        )

    data = {
        "Songa_tenant_id": Songa_tenant_id,
        "provisioning_id": provisioning_id,
        "status": provision.status,
    }

    if provision.status == "Failed":
        frappe.local.response["http_status_code"] = 500

        for step in provision.progress:
            if step.error_message:
                data["error_reason"] = step.error_message

        return api_response(
            False,
            "Tenancy Provisioning Failed",
            500,
            data,
        )

    if provision.status != "Completed":
        return api_response(
            True,
            "Tenancy Provisioning in Progress",
            200,
            data,
        )

    tenant = frappe.get_doc("Tenant", provision.tenant)

    data.update({
        "status": "Success",
        "ERP_tenant_id": tenant.tenant_id,
        "login_url": frappe.utils.get_url("/login"),
        "Administrator": {
            "email": tenant.administrator,
        },
    })

    # Return the temporary password once only.
    password = reset_administrator_password(tenant.administrator)

    data["Administrator"]["temporary_password"] = password

    frappe.db.commit()  # Commit the password change before returning.

    return api_response(
        True,
        "Tenancy Provisioning Success",
        200,
        data,
    )
