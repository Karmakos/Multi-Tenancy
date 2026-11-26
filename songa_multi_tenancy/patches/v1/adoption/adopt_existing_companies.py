
import frappe

from frappe.utils import now_datetime

from songa_multi_tenancy.patches.v1.adoption.utils import (
    get_existing_companies,
    skip_adoption,
    require_doctype,
    has_field,
    set_if_field_exists,
    set_first_available_field,
    set_select_if_valid,
    update_tenant_status,
)


# Configuration

TENANT_DOCTYPE = "Tenant"
TENANT_USER_DOCTYPE = "Tenant User"
ADMIN_DOCTYPE = "Multi Tenancy Administrator"

WORKSPACE_NAME = "Tenants"

SYSTEM_TENANT_ID = "SYSTEM"
SYSTEM_TENANT_TYPE = "System"
CUSTOMER_TENANT_TYPE = "Customer"

SYSTEM_MANAGER_ROLE = "System Manager"  
COMPANY_ADMINISTRATOR_PROFILE = "Company Administrator"
SYSTEM_WIDE_ROLES = {
    "Administrator",
    "Guest",
    "All",
    "System Manager",
    "Multi Tenancy Administrator",
}


# Exclude Guest. Administrator is intentionally included if it exists.
EXCLUDED_USERS = {"Guest"}

LOGGER = frappe.logger("saas_platform")


# ---------------------------------------------------------------------------
# Main patch
# ---------------------------------------------------------------------------

def execute():
    """Adopt existing ERPNext Companies into the multi-tenancy structure."""

    LOGGER.info("Starting multi-tenancy installation setup.")

    try:
        # Platform configuration must exist even on a fresh installation.
        create_company_administrator_role_profile()

        companies = get_existing_companies()

        if not companies:
            skip_adoption()
            return

        # Adopt Companies and Users

        tenants = adopt_companies(companies)

        adopt_existing_users(tenants)

        register_multi_tenancy_administrators()

        grant_multi_tenancy_workspace_access()

        verify_adoption(tenants)

        update_tenant_status(tenants)

        #Add tenant and company fields to shared doctypes
        

        LOGGER.info(
            "Installation adoption completed successfully. "
            "Companies: %s, Tenants: %s",
            len(companies),
            len(tenants),
        )


    except Exception:
        frappe.db.rollback()

        LOGGER.exception(
            "Multi-tenancy installation adoption failed. "
            "All database changes have been rolled back."
        )

        raise


# Company Administrator Role Profile

def create_company_administrator_role_profile():
    """
    Ensure the Company Administrator Role Profile contains all
    currently eligible roles.

    Creates the profile if missing, synchronizes its roles if it
    already exists, and preserves unrelated profile settings.
    """

    require_doctype("Role Profile")

    roles = frappe.get_all(
        "Role",
        filters={"disabled": 0},
        pluck="name",
        order_by="name asc",
    )

    allowed_roles = {
        role
        for role in roles
        if role not in SYSTEM_WIDE_ROLES
    }

    if not allowed_roles:
        frappe.throw(
            "Cannot configure Company Administrator Role Profile: "
            "no eligible roles were found."
        )

    profile = frappe.db.exists(
        "Role Profile",
        COMPANY_ADMINISTRATOR_PROFILE,
    )

    if profile:
        profile = frappe.get_doc(
            "Role Profile",
            COMPANY_ADMINISTRATOR_PROFILE,
        )
        created = False
    else:
        profile = frappe.new_doc("Role Profile")
        profile.role_profile = COMPANY_ADMINISTRATOR_PROFILE
        created = True

    existing_roles = {
        row.role
        for row in profile.roles
        if row.role
    }

    # Add newly eligible roles.
    missing_roles = allowed_roles - existing_roles

    for role in sorted(missing_roles):
        profile.append("roles", {"role": role})

    # Remove disabled or privileged roles.
    for row in list(profile.roles):
        if row.role not in allowed_roles:
            profile.remove(row)

    changed = created or bool(missing_roles) or bool(
        existing_roles - allowed_roles
    )

    if not changed:
        LOGGER.info(
            "Role Profile '%s' is already synchronized.",
            COMPANY_ADMINISTRATOR_PROFILE,
        )
        return profile.name

    # Avoid asynchronous Role Profile update jobs during migration.
    previous_in_install = frappe.flags.in_install

    try:
        frappe.flags.in_install = True

        if created:
            profile.insert(ignore_permissions=True)
        else:
            profile.save(ignore_permissions=True)

    finally:
        frappe.flags.in_install = previous_in_install

    frappe.db.commit()

    LOGGER.info(
        "%s Role Profile '%s': %s roles added, %s roles removed.",
        "Created" if created else "Updated",
        COMPANY_ADMINISTRATOR_PROFILE,
        len(missing_roles),
        len(existing_roles - allowed_roles),
    )

    return profile.name


# Tenant adoption

def adopt_companies(companies):
    """
    Adopt all existing Companies.

    The oldest Company becomes SYSTEM.
    Every other Company becomes an independent customer Tenant.
    """

    require_doctype(TENANT_DOCTYPE)

    tenants = {}

    for index, company in enumerate(companies):
        is_system = index == 0

        tenant_type = (
            SYSTEM_TENANT_TYPE if is_system else CUSTOMER_TENANT_TYPE
        )

        tenant_id = (
            SYSTEM_TENANT_ID
            if is_system
            else generate_tenant_id(company.name)
        )

        tenant = get_or_create_tenant(
            company=company,
            tenant_type=tenant_type,
            tenant_id=tenant_id,
        )

        tenants[company.name] = tenant.name

    return tenants


def generate_tenant_id(company_name):
    """Generate a stable, unique tenant identifier from a Company name."""

    base = frappe.scrub(company_name).upper().replace("_", "-")
    base = base[:35] or "TENANT"

    candidate = base
    counter = 1

    while frappe.db.exists(
        TENANT_DOCTYPE,
        {"tenant_id": candidate},
    ):
        existing = frappe.db.get_value(
            TENANT_DOCTYPE,
            {"tenant_id": candidate},
            "company",
        )

        if existing == company_name:
            return candidate

        counter += 1
        candidate = f"{base[:30]}-{counter}"

    return candidate


def get_or_create_tenant(company, tenant_type, tenant_id):
    """Find or create the Tenant linked to a Company."""

    tenant_name = frappe.db.get_value(
        TENANT_DOCTYPE,
        {"company": company.name},
        "name",
    )

    if tenant_name:
        tenant = frappe.get_doc(TENANT_DOCTYPE, tenant_name)
    else:
        tenant = frappe.new_doc(TENANT_DOCTYPE)

    set_if_field_exists(
        tenant,
        "tenant_name",
        company.company_name or company.name,
    )

    set_if_field_exists(tenant, "tenant_id", tenant_id)
    set_if_field_exists(tenant, "tenant_type", tenant_type)
    set_if_field_exists(tenant, "company", company.name)

    # Active is the operational status. If your Tenant DocType has a
    # separate onboarding/setup status, mark that Complete as well.
    set_select_if_valid(tenant, "status", "Pending")

    set_select_if_valid(tenant, "setup_status", "Complete")
    set_select_if_valid(tenant, "onboarding_status", "Complete")

    if has_field(TENANT_DOCTYPE, "activated_on"):
        tenant.activated_on = tenant.activated_on or now_datetime()

    if tenant.is_new():
        tenant.insert(ignore_permissions=True)
    else:
        tenant.save(ignore_permissions=True)

    return tenant



# User adoption
def get_user_company(user):
    """
    Determine a user's Company from existing User Permissions.

    Rules:
    1. Exactly one Company User Permission: use that Company.
    2. No Company User Permission: use ERPNext Global Default Company.
    3. Multiple Company User Permissions: return None for manual review.
    """

    company_permissions = frappe.get_all(
        "User Permission",
        filters={
            "user": user,
            "allow": "Company",
        },
        pluck="for_value",
    )

    # Remove duplicates and invalid Company references.
    company_permissions = list({
        company
        for company in company_permissions
        if company and frappe.db.exists("Company", company)
    })

    if len(company_permissions) == 1:
        return company_permissions[0]

    if len(company_permissions) > 1:
        LOGGER.warning(
            "Skipping user %s: multiple Company User Permissions: %s",
            user,
            company_permissions,
        )
        return None

    # No explicit Company permission: use ERPNext Global Default Company.
    default_company = frappe.defaults.get_global_default("company")

    if default_company and frappe.db.exists("Company", default_company):
        LOGGER.info(
            "User %s has no explicit Company permission. "
            "Using Global Default Company: %s",
            user,
            default_company,
        )
        return default_company

    LOGGER.warning(
        "Skipping user %s: no Company User Permission and "
        "no valid Global Default Company.",
        user,
    )

    return None


def adopt_existing_users(tenants):
    """Register existing users under their corresponding Tenant."""

    require_doctype(TENANT_USER_DOCTYPE)

    users = frappe.get_all(
        "User",
        filters={
            "name": ["not in", list(EXCLUDED_USERS)]
        },
        fields=[
            "name",
            "role_profile_name",
        ],
    )

    adopted = 0
    skipped = 0

    for user in users:
        company = get_user_company(user.name)

        if not company:
            skipped += 1
            continue

        tenant_name = tenants.get(company)

        if not tenant_name:
            LOGGER.warning(
                "Skipping user %s: Company %s has no adopted Tenant.",
                user.name,
                company,
            )
            skipped += 1
            continue

        tenant = frappe.get_doc(TENANT_DOCTYPE, tenant_name)

        register_tenant_user(
            user=user,
            tenant=tenant,
            company=company,
        )

        ensure_company_permission(
            user=user.name,
            company=company,
        )

        adopted += 1

    LOGGER.info(
        "User adoption completed. Adopted: %s. Skipped: %s.",
        adopted,
        skipped,
    )


def register_tenant_user(user, tenant, company):
    """Create or update the user's Tenant User registration."""

    user_field = find_field(
        TENANT_USER_DOCTYPE,
        ["user", "user_id"],
    )

    tenant_field = find_field(
        TENANT_USER_DOCTYPE,
        ["tenant", "tenant_id"],
    )

    if not user_field or not tenant_field:
        frappe.throw(
            "Tenant User must contain a User link field "
            "('user' or 'user_id') and a Tenant link field "
            "('tenant' or 'tenant_id')."
        )

    existing = frappe.db.get_value(
        TENANT_USER_DOCTYPE,
        {user_field: user.name},
        "name",
    )

    status = frappe.db.get_value(
        "User",
        {"name": user.name},
        "enabled",
    )

    if existing:
        doc = frappe.get_doc(TENANT_USER_DOCTYPE, existing)
    else:
        doc = frappe.new_doc(TENANT_USER_DOCTYPE)

    doc.set(user_field, user.name)
    doc.set(tenant_field, tenant.name)

    set_first_available_field(
        doc,
        ["company"],
        company,
    )

    # Preserve the user's existing Role Profile.
    if user.role_profile_name:
        set_first_available_field(
            doc,
            ["role_profile", "role_profile_name"],
            user.role_profile_name,
        )

    set_select_if_valid(doc, "status", "Active") if status else set_select_if_valid(doc, "status", "Disabled")

    doc.added_on = doc.added_on or now_datetime()
    doc.added_by = doc.added_by or frappe.session.user or"Administrator"

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)


def find_field(doctype, candidates):
    for fieldname in candidates:
        if has_field(doctype, fieldname):
            return fieldname

    return None


def ensure_company_permission(user, company):
    """
    Ensure the user has a Company User Permission.

    Existing permissions are preserved. A missing permission is created
    for the Company determined during adoption.
    """

    existing = frappe.db.exists(
        "User Permission",
        {
            "user": user,
            "allow": "Company",
            "for_value": company,
        },
    )

    if existing:
        return

    permission = frappe.new_doc("User Permission")

    permission.user = user
    permission.allow = "Company"
    permission.for_value = company

    if permission.meta.has_field("apply_to_all_doctypes"):
        permission.apply_to_all_doctypes = 1

    if permission.meta.has_field("is_default"):
        permission.is_default = 1

    permission.insert(ignore_permissions=True)


# Multi Tenancy Administrator registration

def register_multi_tenancy_administrators():
    """Register existing System Manager users as platform administrators."""

    require_doctype(ADMIN_DOCTYPE)

    users = frappe.get_all(
        "User",
        filters={"name": ["not in", list(EXCLUDED_USERS)]},
        pluck="name",
    )

    installation_user = frappe.session.user
    installation_date = now_datetime()

    registered = 0

    for user in users:
        if SYSTEM_MANAGER_ROLE not in frappe.get_roles(user):
            continue

        register_platform_administrator(
            user=user,
            installation_user=installation_user,
            installation_date=installation_date,
        )

        registered += 1

    LOGGER.info(
        "Registered %s existing System Manager users as "
        "Multi Tenancy Administrators.",
        registered,
    )


def register_platform_administrator(
    user,
    installation_user,
    installation_date,
):
    """Create or update a Multi Tenancy Administrator record."""

    status = frappe.db.get_value(
        "User",
        {"name": user},
        "enabled",
    )

    user_field = find_field(
        ADMIN_DOCTYPE,
        ["user", "user_id", "administrator"],
    )

    if not user_field:
        frappe.throw(
            "Multi Tenancy Administrator must have a User link field."
        )

    existing = frappe.db.get_value(
        ADMIN_DOCTYPE,
        {user_field: user},
        "name",
    )

    if existing:
        doc = frappe.get_doc(ADMIN_DOCTYPE, existing)
    else:
        doc = frappe.new_doc(ADMIN_DOCTYPE)

    doc.set(user_field, user)

    set_first_available_field(
        doc,
        ["added_by", "created_by"],
        installation_user,
    )

    set_first_available_field(
        doc,
        ["administrator_level", "level"],
        SYSTEM_MANAGER_ROLE,
    )

    set_first_available_field(
        doc,
        ["added_on", "created_on"],
        installation_date,
    )

    set_select_if_valid(doc, "status", "Active") if status else set_select_if_valid(doc, "status", "Disabled")



    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)


# Workspace access

def grant_multi_tenancy_workspace_access():
    """Ensure System Manager role can access the Multi Tenancy Workspace."""

    if not frappe.db.exists("Workspace", WORKSPACE_NAME):
        frappe.throw(
            f"Workspace '{WORKSPACE_NAME}' does not exist. "
            "Create it before running this patch."
        )

    workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)

    if not workspace.meta.has_field("roles"):
        frappe.throw(
            f"Workspace '{WORKSPACE_NAME}' does not have a roles table."
        )

    existing_roles = {
        row.role for row in workspace.roles
    }

    if SYSTEM_MANAGER_ROLE not in existing_roles:
        workspace.append(
            "roles",
            {"role": SYSTEM_MANAGER_ROLE},
        )

    if workspace.meta.has_field("public"):
        workspace.public = 1

    workspace.save(ignore_permissions=True)

    LOGGER.info(
        "Granted %s access to Workspace %s.",
        SYSTEM_MANAGER_ROLE,
        WORKSPACE_NAME,
    )


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_adoption(tenants):
    """Verify Company-Tenant and User-Tenant consistency."""

    if not tenants:
        frappe.throw("Adoption verification failed: no Tenants were adopted.")

    system_tenants = frappe.get_all(
        TENANT_DOCTYPE,
        filters={"tenant_id": SYSTEM_TENANT_ID},
        fields=["name", "company"],
    )

    if len(system_tenants) != 1:
        frappe.throw(
            "Adoption verification failed: expected exactly one SYSTEM Tenant."
        )

    seen_companies = set()

    for company, tenant_name in tenants.items():
        tenant = frappe.get_doc(TENANT_DOCTYPE, tenant_name)

        if tenant.company != company:
            frappe.throw(
                f"Tenant {tenant.name} is linked to {tenant.company}, "
                f"not the expected Company {company}."
            )

        if company in seen_companies:
            frappe.throw(
                f"Company {company} is linked to more than one Tenant."
            )

        seen_companies.add(company)

        if tenant.tenant_id == SYSTEM_TENANT_ID and tenant.company != company:
            frappe.throw("SYSTEM Tenant Company mismatch.")

    LOGGER.info(
        "Adoption verification successful for %s Tenants.",
        len(tenants),
    )
