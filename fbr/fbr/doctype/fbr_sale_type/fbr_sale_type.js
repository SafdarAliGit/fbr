// Copyright (c) 2025, Safdar Ali and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fbr Sale Type", {
	tax_exempted(frm) {
		if (frm.doc.tax_exempted) {
			frm.set_value("descriptive_tax", "");
		}
	},
});
