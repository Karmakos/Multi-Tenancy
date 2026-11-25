import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class Tenant(Document):
    def suspend(self):
        """Suspend the tenant: disable memberships and member logins."""

        self.status = "Suspended"
        self.suspended_on = now_datetime()
        self.save(ignore_permissions=True)
        self._set_membership_status("Disabled")
        self._set_user_enabled(0)

    def pause(self):
        """Pause the tenant: disable memberships and member logins."""

        self.status = "Paused"
        self.save(ignore_permissions=True)
        self._set_membership_status("Disabled")
        self._set_user_enabled(0)

    def activate(self):
        """Reactivate the tenant and restore its Tenant User memberships."""

        self.status = "Active"
        self.activated_on = now_datetime()
        self.save(ignore_permissions=True)
        self._set_membership_status("Active")
        self._set_user_enabled(1)

    def archive(self):
        """Archive the tenant: disable memberships and member logins."""

        self.status = "Archived"
        self.save(ignore_permissions=True)
        self._set_membership_status("Disabled")
        self._set_user_enabled(0)

    def mark_deleted(self):
        """Soft-delete the tenant: block access and disable logins.

        All data is preserved; member Users are disabled so they
        cannot sign in.
        """

        self.status = "Deleted"
        self.save(ignore_permissions=True)
        self._set_membership_status("Disabled")
        self._set_user_enabled(0)

    def _member_users(self):
        """All Users belonging to this tenant.

        Union of Tenant User memberships, the tenant Administrator,
        and Users holding a Company User Permission for the
        tenant's Company — the membership table alone is incomplete.
        """

        users = set(
            frappe.get_all(
                "Tenant User",
                filters={"tenant": self.name},
                pluck="user",
            )
        )

        if self.administrator:
            users.add(self.administrator)

        if self.company:
            users.update(
                frappe.get_all(
                    "User Permission",
                    filters={
                        "allow": "Company",
                        "for_value": self.company,
                    },
                    pluck="user",
                )
            )

        users.discard(None)
        users -= {"Administrator", "Guest"}
        return users

    def _set_user_enabled(self, enabled):
        for user in self._member_users():
            frappe.db.set_value("User", user, "enabled", enabled)

    def _set_membership_status(self, status):
        for name in frappe.get_all(
            "Tenant User",
            filters={"tenant": self.name},
            pluck="name",
        ):
            frappe.db.set_value("Tenant User", name, "status", status)

    def on_trash(self):
        """Cascade-delete everything owned by this tenant."""

        self._delete_scoped_records()
        self._delete_company_history()
        self._delete_company()
        self._delete_exclusive_users()
        self._delete_memberships()

    def _delete_scoped_records(self):
        """Delete records carrying this tenant's tenant link."""

        doctypes = frappe.get_all(
            "Custom Field",
            filters={
                "fieldname": "tenant",
                "fieldtype": "Link",
                "options": "Tenant",
            },
            pluck="dt",
        )

        for doctype in doctypes:
            if not frappe.db.exists("DocType", doctype):
                continue

            names = frappe.get_all(
                doctype,
                filters={"tenant": self.name},
                pluck="name",
            )

            for name in names:
                frappe.delete_doc(
                    doctype,
                    name,
                    ignore_permissions=True,
                    force=True,
                )

    def _company_scoped_doctypes(self):
        """DocTypes with a company Link field, standard or custom."""

        doctypes = set(
            frappe.get_all(
                "DocField",
                filters={
                    "fieldname": "company",
                    "fieldtype": "Link",
                    "options": "Company",
                },
                pluck="dt",
            )
        )
        doctypes.update(
            frappe.get_all(
                "Custom Field",
                filters={
                    "fieldname": "company",
                    "fieldtype": "Link",
                    "options": "Company",
                },
                pluck="dt",
            )
        )
        return doctypes

    def _delete_company_history(self):
        """Delete every record belonging to this tenant's Company."""

        if not self.company:
            return

        for doctype in self._company_scoped_doctypes():
            if not frappe.db.exists("DocType", doctype):
                continue

            names = frappe.get_all(
                doctype,
                filters={"company": self.company},
                pluck="name",
            )

            for name in names:
                frappe.delete_doc(
                    doctype,
                    name,
                    ignore_permissions=True,
                    force=True,
                )

    def _delete_company(self):
        if self.company and frappe.db.exists("Company", self.company):
            frappe.delete_doc(
                "Company",
                self.company,
                ignore_permissions=True,
            )

    def _delete_user_permissions(self, users, deletable):
        """Remove User Permissions held by the tenant's Users.

        All permissions are removed for Users being deleted; for
        shared Users only permissions targeting this tenant's
        Company are removed.
        """

        names = set(
            frappe.get_all(
                "User Permission",
                filters={"user": ["in", list(deletable)]},
                pluck="name",
            )
        )

        if self.company:
            names.update(
                frappe.get_all(
                    "User Permission",
                    filters={
                        "user": ["in", list(users)],
                        "allow": "Company",
                        "for_value": self.company,
                    },
                    pluck="name",
                )
            )

        for name in names:
            frappe.delete_doc(
                "User Permission",
                name,
                ignore_permissions=True,
                force=True,
            )

    def _delete_exclusive_users(self):
        """Delete Users whose only tenant membership is this tenant."""

        member_users = self._member_users()

        users = set(
            frappe.get_all(
                "Tenant User",
                filters={"tenant": self.name},
                pluck="user",
            )
        )

        deletable = set()

        for user in users:
            if not user or user in ("Administrator", "Guest"):
                continue

            other_memberships = frappe.get_all(
                "Tenant User",
                filters={"user": user, "tenant": ["!=", self.name]},
                pluck="name",
            )

            if not other_memberships:
                deletable.add(user)

        self._delete_user_permissions(member_users, deletable)

        for user in deletable:
            try:
                frappe.delete_doc("User", user, ignore_permissions=True)
            except Exception:
                frappe.log_error(
                    title=f"Tenant {self.name}: could not delete User {user}",
                )

    def _delete_memberships(self):
        for name in frappe.get_all(
            "Tenant User",
            filters={"tenant": self.name},
            pluck="name",
        ):
            frappe.delete_doc(
                "Tenant User",
                name,
                ignore_permissions=True,
                force=True,
            )
