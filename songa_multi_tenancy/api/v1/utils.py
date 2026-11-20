import frappe
import secrets
import string

from frappe.utils.password import update_password


def reset_administrator_password(administrator_email):
    if not administrator_email:
        frappe.throw("Administrator Email is required.")

    if not frappe.db.exists("User", administrator_email):
        frappe.throw("Administrator User does not exist.")

    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    password = "".join(secrets.choice(alphabet) for _ in range(20))

    update_password(
        user=administrator_email,
        pwd=password,
        logout_all_sessions=True,
    )

    return password