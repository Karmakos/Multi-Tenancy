
import frappe
from frappe import _
from frappe.utils import now_datetime
from songa_multi_tenancy.patches.v1.adoption.adopt_existing_companies import create_company_administrator_role_profile

ROLE_PROFILE = "Company Administrator"

PROVISIONING_STEPS = [
    "Create Company",
    "Create Administrator User",
    "Assign Company Administrator Role",
    "Apply Company User Permission",
    "Create Tenant",
    "Activate Tenant",
]


def process_tenant_provisioning(
    provisioning_name,
    company_name,
    admin_email,
    admin_phone,
    admin_full_name,
):
    """
    Execute tenant provisioning sequentially.

    Each successful step is committed independently so that
    provisioning progress and previously created records survive
    a later failure.
    """

    provision = frappe.get_doc(
        "Tenant Provisioning",
        provisioning_name,
    )

    if provision.status == "Completed":
        return

    if provision.status == "In Progress":
        # Avoid concurrent execution of the same request.
        return

    provision.status = "In Progress"
    provision.started_on = now_datetime()
    provision.save(ignore_permissions=True)

    try:
        # Step 1: Company.
        run_step(
            provisioning_name,
            1,
            lambda p: create_company(p, company_name),
        )

        # Step 2: Administrator.
        run_step(
            provisioning_name,
            2,
            lambda p: create_administrator(
                p,
                admin_email,
                admin_phone,
                admin_full_name,
            ),
        )

        # Step 3: Role Profile.
        run_step(
            provisioning_name,
            3,
            lambda p: assign_company_administrator_role(
                p,
                admin_email,
            ),
        )

        # Step 4: Company User Permission.
        run_step(
            provisioning_name,
            4,
            lambda p: apply_company_user_permission(
                p,
                admin_email,
                company_name
            ),
        )

        # Step 5: Tenant.
        run_step(
            provisioning_name,
            5,
            lambda p: create_tenant(
                p,
                company_name,
                admin_email,
            ),
        )

        # Step 6: Activate.
        run_step(
            provisioning_name,
            6,
            lambda p: activate_tenant(
                p,
                company_name, 
                admin_email
                ),
        )

    except Exception:
        frappe.db.rollback()
        raise


def run_step(provisioning_name, sequence, operation):
    """Run and persist the lifecycle of an individual step."""

    provision = frappe.get_doc(
        "Tenant Provisioning",
        provisioning_name,
    )

    row = next(
        (
            item for item in provision.progress
            if item.sequence == sequence
        ),
        None,
    )

    if not row:
        frappe.throw(
            _("Provisioning step {0} does not exist.").format(sequence)
        )

    if row.status == "Completed":
        return

    row.status = "In Progress"
    row.started_on = now_datetime()
    row.completed_on = None
    row.error_message = None

    provision.status = "In Progress"
    provision.save(ignore_permissions=True)
    frappe.db.commit()

    try:
        # Reload after committing the step's In Progress state.
        provision = frappe.get_doc(
            "Tenant Provisioning",
            provisioning_name,
        )

        operation(provision)

        # Reload to capture changes made by the operation.
        provision = frappe.get_doc(
            "Tenant Provisioning",
            provisioning_name,
        )

        row = next(
            item for item in provision.progress
            if item.sequence == sequence
        )

        row.status = "Completed"
        row.completed_on = now_datetime()
        row.error_message = None

        provision.save(ignore_permissions=True)
        frappe.db.commit()

    except Exception as exc:
        frappe.db.rollback()

        provision = frappe.get_doc(
            "Tenant Provisioning",
            provisioning_name,
        )

        row = next(
            item for item in provision.progress
            if item.sequence == sequence
        )

        row.status = "Failed"
        row.completed_on = now_datetime()
        row.error_message = str(exc)[:10000]

        provision.status = "Failed"
        provision.error_message = (
            f"{PROVISIONING_STEPS[sequence - 1]}: {exc}"
        )[:10000]
        provision.completed_on = now_datetime()

        provision.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.log_error(
            frappe.get_traceback(),
            f"Tenant Provisioning Failed: {provision.provisioning_id}",
        )

        raise


def create_company(provision, company_name):
    """Create the ERPNext Company."""

    company = frappe.db.get_value(
        "Company",
        {"company_name": company_name},
        "name"
    )

    if company:
        frappe.throw(
            _("Company {0} already exists.").format(company_name),
            frappe.DuplicateEntryError
        )

    country = frappe.defaults.get_global_default("country")
    currency = frappe.defaults.get_global_default("currency")

    if not country or not currency:
        frappe.throw(
            _("Configure the site's default country and currency "
              "before provisioning tenants.")
        )

    # Generate a short, unique abbreviation.
    base_abbr = "".join(
        word[0] for word in company_name.split() if word
    ).upper()[:5] or "COMP"

    abbr = base_abbr
    suffix = 1

    while frappe.db.exists("Company", {"abbr": abbr}):
        suffix += 1
        abbr = f"{base_abbr[:3]}{suffix}"

    company = frappe.new_doc("Company")
    company.company_name = company_name
    company.abbr = abbr
    company.country = country
    company.default_currency = currency
    company.insert(ignore_permissions=True)

    provision.company = company.name
    provision.save(ignore_permissions=True)


def create_administrator(
    provision,
    email,
    phone,
    full_name,
):
    """Create the tenant's initial administrator User."""

    if frappe.db.exists("User", email):
        frappe.throw(
            _("Administrator email {0} is already registered.").format(email)
        )

    names = full_name.split(maxsplit=1)

    user = frappe.new_doc("User")
    user.email = email
    user.first_name = names[0]
    user.last_name = names[1] if len(names) > 1 else ""
    user.phone = phone.replace("+", "")
    user.enabled = 1
    user.user_type = "System User"
    user.send_welcome_email = 0


    user.insert(ignore_permissions=True, ignore_mandatory=True)

    provision.administrator = user.name
    provision.save(ignore_permissions=True)


def assign_company_administrator_role(provision, admin_email):
    """Assign the Company Administrator Role Profile."""

    if not frappe.db.exists("User", admin_email):
        frappe.throw(_("Administrator User has not been created."))

    if not frappe.db.exists("Role Profile", ROLE_PROFILE):
        create_company_administrator_role_profile()
        frappe.log_error(
                message=frappe.get_traceback(), 
                title=_("Role Profile {0} does not exist.").format(ROLE_PROFILE)
            )

    user = frappe.get_doc("User", admin_email)
    user.role_profile_name = ROLE_PROFILE
    user.save(ignore_permissions=True)


def apply_company_user_permission(provision, admin_email, company_name):
    """Restrict the administrator to the newly created Company."""

    if not frappe.db.exists("User", admin_email) or not frappe.db.exists("Company", company_name):
        frappe.throw(
            _("Company and Administrator must exist before "
              "applying Company User Permission.")
        )

    existing = frappe.db.exists(
        "User Permission",
        {
            "user": admin_email,
            "allow": "Company",
            "for_value": company_name,
        },
    )

    if existing:
        frappe.db.set_value(
            "User Permission",
            existing,
            {
                "is_default": 1,
                "apply_to_all_doctypes": 1,
            },
        )
        return

    permission = frappe.new_doc("User Permission")
    permission.user = admin_email
    permission.allow = "Company"
    permission.for_value = company_name
    permission.is_default = 1
    permission.apply_to_all_doctypes = 1
    permission.insert(ignore_permissions=True)

    # Set the user's Company default as well.
    frappe.defaults.add_default(
        "company",
        company_name,
        admin_email,
    )


def create_tenant(provision, company_name, admin_email):
    """Create and link the Tenant."""

    if provision.tenant:
        return

    tenant_id = frappe.generate_hash(length=12)

    tenant = frappe.new_doc("Tenant")
    tenant.tenant_name = company_name
    tenant.tenant_id = tenant_id
    tenant.songa_tenant_id = provision.songa_tenant_id
    tenant.tenant_type = "Customer"
    tenant.tenant_category = provision.tenant_category
    tenant.company = company_name
    tenant.administrator = admin_email
    tenant.status = "Pending"

    tenant.insert(ignore_permissions=True)

    provision.tenant = tenant.name

    # Link all provisioning steps to the resulting Tenant.
    # for row in provision.progress:
    #     row.tenant = tenant.name

    provision.save(ignore_permissions=True)


def activate_tenant(provision, company_name, admin_email):
    """Activate the Tenant and complete provisioning."""

    if not provision.tenant:
        frappe.throw(_("Tenant has not been created."))

    if not company_name or not admin_email:
        frappe.throw(_("Company or Administrator is missing."))

    # Verify the Company relationship.
    tenant = frappe.get_doc("Tenant", provision.tenant)

    if tenant.company != company_name:
        frappe.throw(_("Tenant Company relationship is invalid."))

    if tenant.administrator != admin_email:
        frappe.throw(_("Tenant Administrator relationship is invalid."))

    # Activate only after all preceding steps have completed.
    tenant.status = "Active"
    tenant.activated_on = now_datetime()
    tenant.save(ignore_permissions=True)

    provision.status = "Completed"
    provision.completed_on = now_datetime()
    provision.error_message = None
    provision.save(ignore_permissions=True)
