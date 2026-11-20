# Copyright (c) 2026, Acube and Contributors
# See license.txt
"""PF Detailed Log: the EPF wages of the schemes on the wage ceiling (EPS-1250 ER-550, EPS-0 ER-1800 - the FTC
employees) follow the Statutory Wage Ceiling of the month: Rs. 15,000 at present, Rs. 25,000 when it is raised.

bench --site batl run-tests --module a3_finance.tests.test_pf_wage_ceiling

Works out the site's own PF Detailed Logs again without saving them; the ceiling set for the test is rolled back.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from a3_finance.a3_finance.doctype.employee_pension_scheme.employee_pension_scheme import (
	CEILING_EPS_ER,
	CEILING_ER_ONLY,
)


class TestPFWageCeiling(FrappeTestCase):
	def setUp(self):
		frappe.db.savepoint("pf_ceiling")

	def tearDown(self):
		frappe.db.rollback(save_point="pf_ceiling")

	def logs_of(self, calculation):
		"""A month's logs of employees on the scheme with this calculation, with wages above Rs. 25,000."""
		return frappe.db.sql(
			"""
			select l.name, l.payroll_month, l.payroll_year
			from `tabPF Detailed Log` l
			join `tabEmployee` e on e.name = l.employee
			join `tabEmployee Pension Scheme` s on s.name = e.custom_employee_pension_scheme
			where s.calculation = %s and ifnull(l.payroll_month, '') != '' and ifnull(l.payroll_year, '') != ''
			order by l.payroll_year desc, l.payroll_month desc
			limit 20
			""",
			calculation,
			as_dict=True,
		)

	def set_ceiling(self, log, ceiling):
		setting = frappe.db.get_value(
			"Payroll Master Setting",
			{"payroll_year": str(log.payroll_year), "payroll_month_number": int(log.payroll_month)},
		)
		if not setting:
			self.skipTest("no Payroll Master Setting for the month")
		frappe.db.set_value("Payroll Master Setting", setting, "edli_wages", ceiling)

	def worked_out(self, name):
		doc = frappe.get_doc("PF Detailed Log", name)
		doc.calculate_epf_wages()
		return doc

	def check(self, calculation, expected):
		logs = self.logs_of(calculation)
		if not logs:
			self.skipTest(f"no PF Detailed Log for {calculation}")
		checked = 0
		for ceiling, (epf, eps_wages, eps, er) in expected.items():
			self.set_ceiling(logs[0], ceiling)
			for log in logs:
				if (log.payroll_month, log.payroll_year) != (logs[0].payroll_month, logs[0].payroll_year):
					continue
				doc = self.worked_out(log.name)
				wages = doc.base + doc.service_weightage + doc.da  # roughly the full EPF wages
				if wages < 26000:
					continue  # below the higher ceiling: wages are not capped
				self.assertEqual(doc.epf_wages, epf, f"{log.name} at {ceiling or 15000}")
				self.assertEqual(doc.eps_wages, eps_wages, log.name)
				self.assertEqual(doc.edli_wages, ceiling or 15000, log.name)
				self.assertEqual(round(doc.eps), eps, log.name)
				self.assertEqual(doc.er, er, log.name)
				checked += 1
		if not checked:
			self.skipTest("no employee with wages above Rs. 25,000")

	def test_eps_1250_er_550(self):
		# ceiling 0 = Rs. 15,000
		self.check(CEILING_EPS_ER, {0: (15000, 15000, 1250, 550), 25000: (25000, 25000, 2083, 917)})

	def test_eps_0_er_1800(self):
		self.check(CEILING_ER_ONLY, {0: (15000, 0, 0, 1800), 25000: (25000, 0, 0, 3000)})
