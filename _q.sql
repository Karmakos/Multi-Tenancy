SELECT name, parent, role FROM `tabHas Role` WHERE parent IN ('nutan+5002@antarcticaglobal.com','admin@amecteoetptpilc.com','j.murigi@songa.mobi');
SELECT * FROM `tabMulti Tenancy Administrator`;
SELECT tu.user, tu.tenant, tu.status, t.status AS tenant_status, t.tenant_name FROM `tabTenant User` tu LEFT JOIN `tabTenant` t ON t.name = tu.tenant WHERE tu.user IN ('nutan+5002@antarcticaglobal.com','admin@amecteoetptpilc.com');
