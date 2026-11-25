SELECT name, tenant_name, status, company, administrator FROM `tabTenant`;
SELECT name, user, allow, for_value, is_default FROM `tabUser Permission` WHERE allow = 'Company';
SELECT name, email, enabled, role_profile_name FROM `tabUser` WHERE role_profile_name = 'Company Administrator' LIMIT 10;
