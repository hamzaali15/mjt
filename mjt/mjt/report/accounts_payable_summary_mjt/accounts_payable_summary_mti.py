# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from mjt.mjt.report.accounts_receivable_summary_mjt.accounts_receivable_summary_mjt \
	import AccountsReceivableSummaryMJT

def execute(filters=None):
	args = {
		"party_type": "Supplier",
		"naming_by": ["Buying Settings", "supp_master_name"],
	}
	return AccountsReceivableSummaryMJT(filters).run(args)

