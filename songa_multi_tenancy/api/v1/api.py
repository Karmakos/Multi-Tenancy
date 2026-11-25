
import frappe
from frappe import _
from frappe.utils import now_datetime

from songa_multi_tenancy.api.v1.provisioning import PROVISIONING_STEPS
from songa_multi_tenancy.api.v1.utils import reset_administrator_password
from songa_multi_tenancy.permissions import _user_company

MAX_RETRIES = 3


def api_response(success, message, status_code, data=None):
    """Standard response envelope."""

    frappe.local.response["http_status_code"] = status_code

    return {
        "Success": success,
        "Message": message,
        "Status_code": status_code,
        "Data": data or {},
    }


def enqueue_provisioning(provision, company_name, email, phone, full_name):
    """Queue the provisioning worker for a Tenant Provisioning doc."""

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


def requeue_failed_provisioning(provision, company_name, email, phone, full_name):
    """
    Reset a Failed provisioning request and enqueue it again.

    Completed steps are preserved and skipped by the worker, so
    provisioning resumes where it left off.
    """

    retry_count = provision.retry_count or 0

    if retry_count >= MAX_RETRIES:
        return api_response(
            False,
            "Maximum provisioning retries exceeded.",
            409,
            {
                "Songa_tenant_id": provision.songa_tenant_id,
                "provisioning_id": provision.provisioning_id,
                "status": provision.status,
                "retry_count": retry_count,
            },
        )

    provision.retry_count = retry_count + 1
    provision.status = "Queued"
    provision.started_on = now_datetime()
    provision.completed_on = None
    provision.error_message = None
    provision.password_retrieved = 0
    provision.save(ignore_permissions=True)

    # The reset must be committed before the worker starts.
    frappe.db.commit()

    enqueue_provisioning(
        provision,
        company_name,
        email,
        phone,
        full_name,
    )

    return api_response(
        True,
        "Tenancy Provisioning Re-queued successfully",
        202,
        {
            "Songa_tenant_id": provision.songa_tenant_id,
            "provisioning_id": provision.provisioning_id,
            "status": "Queued",
        },
    )


@frappe.whitelist(methods=["POST"])
def register_tenant():
    """
    Accept a tenant registration request and enqueue provisioning.
    """

    try:
        payload = frappe.request.get_json(silent=True)

        if not isinstance(payload, dict):
            frappe.throw(
                _("Request body must be a JSON object."),
                frappe.ValidationError,
            )

        songa_tenant_id = payload.get("songa_tenant_id")
        company_name = payload.get("company")
        tenant_category = payload.get("tenant_category")
        admin = payload.get("admin") or {}

        email = (admin.get("email") or "").strip().lower()
        phone = admin.get("phone")
        full_name = (admin.get("full_name") or "").strip()

        # This is to be handled properly
        modules = payload.get("selected_songa_modules") or []

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

        existing_provision = frappe.get_all(
            "Tenant Provisioning",
            filters={},
            or_filters=[
                {"songa_tenant_id": songa_tenant_id},
                {"company": company_name},
            ],
            fields=["name", "provisioning_id", "status"],
            limit=1,
        )

        existing_provision = existing_provision[0] if existing_provision else None

        if existing_provision:
            # A Failed request can be retried; anything else is a duplicate.
            if existing_provision.status == "Failed":
                provision = frappe.get_doc(
                    "Tenant Provisioning",
                    existing_provision.name,
                )

                # Prefer the originally registered payload; fall back to
                # the values supplied in this request.
                original = provision.payload or {}

                if isinstance(original, str):
                    original = frappe.parse_json(original)

                if not isinstance(original, dict):
                    original = {}


                original_admin = original.get("admin") or {}

                return requeue_failed_provisioning(
                    provision,
                    original.get("company") or company_name,
                    (original_admin.get("email") or "").strip().lower() or email,
                    original_admin.get("phone") or phone,
                    (original_admin.get("full_name") or "").strip() or full_name,
                )

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

        if frappe.db.exists("Tenant", {"songa_tenant_id": songa_tenant_id}):
            frappe.throw(
                _("This Songa Tenant ID is already registered.")
            )

        if frappe.db.exists("User", email) and _user_company(email):
            frappe.throw(
                _("The administrator email is already registered.")
            )

        provision = frappe.new_doc("Tenant Provisioning")
        provision.company = None
        provision.songa_tenant_id = songa_tenant_id
        provision.provisioning_id = frappe.generate_hash(length=20)
        provision.tenant_category = tenant_category
        provision.status = "Queued"
        provision.started_on = now_datetime()
        provision.payload = payload

        for sequence, step_name in enumerate(PROVISIONING_STEPS, start=1):
            provision.append(
                "progress",
                {
                    "step_name": step_name,
                    "sequence": sequence,
                },
            )

        try:
            provision.insert(ignore_permissions=True)
        except frappe.DuplicateEntryError:
            # Lost a race against a concurrent registration.
            frappe.db.rollback()
            return api_response(
                False,
                "A provisioning request already exists.",
                409,
                {"Songa_tenant_id": songa_tenant_id},
            )

        enqueue_provisioning(
            provision,
            company_name,
            email,
            phone,
            full_name,
        )

        # The request must be committed before the worker starts.
        frappe.db.commit()

        return api_response(
            True,
            "Tenancy Provisioning Queued successfully",
            202,
            {
                "Songa_tenant_id": songa_tenant_id,
                "provisioning_id": provision.provisioning_id,
                "status": "Queued",
            },
        )

    except frappe.ValidationError:
        frappe.db.rollback()
        raise

    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            frappe.get_traceback(),
            "Tenant Registration API Error",
        )
        raise


@frappe.whitelist(methods=["GET"])
def get_tenant_provisioning_status(
    songa_tenant_id,
    provisioning_id,
):
    """Return the current state of a tenant provisioning request."""

    songa_tenant_id = (songa_tenant_id or "").strip()
    provisioning_id = (provisioning_id or "").strip()

    if not songa_tenant_id or not provisioning_id:
        return api_response(
            False,
            "Both songa_tenant_id and provisioning_id are required.",
            400,
        )

    provision = frappe.db.get_value(
        "Tenant Provisioning",
        {
            "songa_tenant_id": songa_tenant_id,
            "provisioning_id": provisioning_id,
        },
        ["name", "status", "tenant", "password_retrieved"],
        as_dict=True,
    )

    if not provision:
        return api_response(
            False,
            "Provisioning ID Request Not Found.",
            404,
        )

    data = {
        "Songa_tenant_id": songa_tenant_id,
        "provisioning_id": provisioning_id,
        "status": provision.status,
    }

    if provision.status == "Failed":
        # get_value does not load child rows; fetch the full doc.
        doc = frappe.get_doc("Tenant Provisioning", provision.name)

        for step in doc.progress:
            if step.error_message:
                data["error_reason"] = step.error_message
                break

        if doc.error_message:
            data["error_reason"] = doc.error_message

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
    if provision.password_retrieved:
        data["Administrator"]["credentials_status"] = "already_retrieved"
        return api_response(
            True,
            "Tenancy Provisioning Success",
            200,
            data,
        )

    password = reset_administrator_password(tenant.administrator)

    doc = frappe.get_doc("Tenant Provisioning", provision.name)
    doc.password_retrieved = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()  # Commit the password change before returning.

    data["Administrator"]["temporary_password"] = password

    return api_response(
        True,
        "Tenancy Provisioning Success",
        200,
        data,
    )
