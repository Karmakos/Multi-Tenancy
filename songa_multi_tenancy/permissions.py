import frappe


def get_user_tenant(user=None):
    user = user or frappe.session.user

    return frappe.db.get_value(
        "Tenant User",
        {"user": user, "status": "Active"},
        "tenant",
    )


def is_platform_admin(user=None):
    user = user or frappe.session.user

    return bool(
        frappe.db.exists(
            "Company Administrator",
            {"user": user, "status": "Active"},
        )
    )

#DocType specific permission query functions for multi-tenancy scoping
def item_query(user=None):
    user = user or frappe.session.user

    if user == "Administrator" or is_platform_admin(user):
        return ""

    tenant = get_user_tenant(user)

    if not tenant:
        return "1=0"

    return "`tabItem`.`tenant` = {0}".format(
        frappe.db.escape(tenant)
    )


def item_group_query(user=None):
    user = user or frappe.session.user

    if user == "Administrator" or is_platform_admin(user):
        return ""

    tenant = get_user_tenant(user)

    if not tenant:
        return "1=0"

    return "`tabItem Group`.`tenant` = {0}".format(
        frappe.db.escape(tenant)
    )

def customer_query(user=None):
    user = user or frappe.session.user

    if user == "Administrator" or is_platform_admin(user):
        return ""

    tenant = get_user_tenant(user)

    if not tenant:
        return "1=0"

    return "`tabCustomer`.`tenant` = {0}".format(
        frappe.db.escape(tenant)
    )

def supplier_query(user=None):
    user = user or frappe.session.user

    if user == "Administrator" or is_platform_admin(user):
        return ""

    tenant = get_user_tenant(user)

    if not tenant:
        return "1=0"

    return "`tabSupplier`.`tenant` = {0}".format(
        frappe.db.escape(tenant)
    )

def brand_query(user=None):
    user = user or frappe.session.user

    if user == "Administrator" or is_platform_admin(user):
        return ""

    tenant = get_user_tenant(user)

    if not tenant:
        return "1=0"

    return "`tabBrand`.`tenant` = {0}".format(
        frappe.db.escape(tenant)
    )

def price_list_query(user=None):
    user = user or frappe.session.user

    if user == "Administrator" or is_platform_admin(user):
        return ""

    tenant = get_user_tenant(user)

    if not tenant:
        return "1=0"

    return "`tabPrice List`.`tenant` = {0}".format(
        frappe.db.escape(tenant)
    )

def item_price_query(user=None):
    user = user or frappe.session.user

    if user == "Administrator" or is_platform_admin(user):
        return ""

    tenant = get_user_tenant(user)

    if not tenant:
        return "1=0"

    return "`tabItem Price`.`tenant` = {0}".format(
        frappe.db.escape(tenant)
    )


def user_query(user):
    """
    Restricts the User list view so that:
    - Global Administrators and System Managers see all users.
    - Company Administrators and standard users only see users 
      belonging to their assigned tenant/company.
    """
    user = user or frappe.session.user

    # Bypass restriction for global tech/system admins
    if user == "Administrator" or "System Manager" in frappe.get_roles(user):
        return "" # Sees all users site-wide

    # Find the tenant linked to this user
    tenant = frappe.db.get_value(
        "Tenant User",
        {"user": user},
        "tenant"
    )

    if not tenant:
        return "1=0" # No tenant assigned, sees nothing

    # Find all user IDs linked to this same tenant
    tenant_users = frappe.get_all(
        "Tenant User",
        filters={"tenant": tenant},
        pluck="user"
    )

    if not tenant_users:
        return "1=0"

    escaped_users = ", ".join([frappe.db.escape(u) for u in tenant_users])

    # Restrict User list to only users within the same tenant
    return f"`tabUser`.`name` IN ({escaped_users})"

#Doc level permission check for multi-tenancy scoping
def tenant_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user

    if user == "Administrator" or is_platform_admin(user):
        return None

    tenant = get_user_tenant(user)

    if not tenant:
        return False

    if doc.get("tenant") != tenant:
        return False

    return None


#Doc level permission check for User doctype

def user_has_permission(doc, ptype="read", user=None):
    user = user or frappe.session.user

    # Global admins have full access
    if user == "Administrator" or "System Manager" in frappe.get_roles(user):
        return True

    # Users can always view/edit their own profile
    if doc.name == user:
        return True

    # Check if current user is a Company Administrator
    is_company_admin = "Company Administrator" in frappe.get_roles(user)
    
    # Get target user's tenant vs current user's tenant
    target_tenant = frappe.db.get_value("Tenant User", {"user": doc.name}, "tenant")
    current_tenant = frappe.db.get_value("Tenant User", {"user": user}, "tenant")

    # Allow access if both belong to the same tenant and the user has Company Administrator role
    if is_company_admin and target_tenant and current_tenant and target_tenant == current_tenant:
        return True

    return False


