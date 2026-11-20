"""Report export (Export in a report's menu) sent as a standard file download.

Frappe sends the exported file as application/octet-stream with the header Content-Disposition: filename="..." -
without the disposition type the standard requires (RFC 6266) - and with every filter value in the file name
(commas, slashes, accents). A browser, antivirus or proxy that rejects the header saves the file under a random name
without an extension, which Excel then does not open. Here the file is sent as an attachment with its real type
(.xlsx / .csv) and a short Windows-safe name; Frappe makes the content as before.

The ageing reports (Accounts Payable / Receivable and their Summaries, Stock Ageing) and the Trial Balance are laid
out for Excel here: amounts and quantities as numbers with 2 decimals and thousands separators, days as whole
numbers, dates as dates, a bold and frozen header row with a filter, and the report filters above the table when
"Include filters" is ticked. In the Trial Balance the group accounts (and the total) are bold, as on screen.

BrahMos Reports & Observations Tracker, points 3, 4, 5 (export) and 27 (Trial Balance in bold).
"""

import json
import math
import re
import unicodedata
from datetime import date, datetime
from io import BytesIO

import frappe
from frappe.utils import cint, cstr

MIME_TYPES = {
	"xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
	"csv": "text/csv; charset=utf-8",
}
FORMATTED_REPORTS = (
	"Accounts Payable",
	"Accounts Payable Summary",
	"Accounts Receivable",
	"Accounts Receivable Summary",
	"Stock Ageing",
	"Trial Balance",
)
AMOUNT_FORMAT = "#,##0.00"
WHOLE_NUMBER_FORMAT = "0"
EXCEL_TEXT_LIMIT = 32767  # longer text makes Excel repair the file


@frappe.whitelist()
def export_query():
	"""frappe.desk.query_report.export_query (override_whitelisted_methods), with the file sent as a download."""
	from frappe.desk import query_report

	try:
		from frappe.desk.query_report import _export_query, build_xlsx_data, format_fields, run
		from frappe.desk.reportview import clean_params, parse_json
		from frappe.desk.utils import pop_csv_params
	except ImportError:
		# a Frappe update moved these: export as Frappe does, and log it
		frappe.log_error(title="Report export override not applied (Frappe export helpers changed)")
		return query_report.export_query()

	form_params = frappe._dict(frappe.local.form_dict)
	if cint(form_params.export_in_background):
		# emailed as a link to a File: Frappe's own job
		return query_report.export_query()

	csv_params = pop_csv_params(form_params)
	clean_params(form_params)
	parse_json(form_params)
	frappe.permissions.can_export(
		frappe.get_cached_value("Report", form_params.report_name, "ref_doctype"), raise_exception=True
	)

	if form_params.report_name in FORMATTED_REPORTS and form_params.file_format_type == "Excel":
		result = export_formatted_xlsx(form_params)
	else:
		result = query_report._export_query(form_params, csv_params, populate_response=False)
	if not result:
		# no columns: Frappe has shown "No data to export"
		return
	file_name, extension, content = result
	send_file(file_name, extension, content)


def send_file(file_name, extension, content):
	"""Content-Type of the file, Content-Disposition: attachment; filename="<safe name>"."""
	frappe.response["type"] = "download"
	frappe.response["filename"] = safe_filename(file_name, extension)
	frappe.response["filecontent"] = content
	frappe.response["content_type"] = MIME_TYPES.get(extension, "application/octet-stream")
	frappe.response["display_content_as"] = "attachment"


def safe_filename(name, extension):
	"""A name Windows, macOS and Linux all accept, in plain ASCII: 'Accounts Payable_2026-11-12_Due Date.xlsx'."""
	name = unicodedata.normalize("NFKD", cstr(name)).encode("ascii", "ignore").decode()
	name = re.sub(r"[^A-Za-z0-9 ._()&-]+", "_", name)  # also , / \ : * ? " < > | and control characters
	name = re.sub(r"\s*_[\s_]*", "_", name)
	name = re.sub(r"\s+", " ", name).strip(" ._")[:120].rstrip(" ._") or "Report"
	return f"{name}.{extension}"


def export_formatted_xlsx(form_params):
	"""(file name, 'xlsx', content) of the report as Frappe exports it (same rows, columns and filters), laid out
	for Excel."""
	from frappe.desk.query_report import build_xlsx_data, format_fields, run

	report_name = form_params.report_name
	visible_idx = form_params.visible_idx or []
	if isinstance(visible_idx, str):
		visible_idx = json.loads(visible_idx)

	data = frappe._dict(
		run(
			report_name,
			form_params.filters,
			custom_columns=frappe.parse_json(form_params.custom_columns or "[]"),
			are_default_filters=False,
		)
	)
	if not data.columns:
		frappe.respond_as_web_page(
			frappe._("No data to export"), frappe._("You can try changing the filters of your report.")
		)
		return None
	data.filters = form_params.applied_filters
	format_fields(data)

	table, widths = build_xlsx_data(
		data, visible_idx, cint(form_params.include_indentation), include_filters=False
	)
	columns = [column for column in data.columns if not column.get("hidden")]
	filters = data.filters if cint(form_params.include_filters) else None
	bold_rows = (
		BOLD_ROWS[report_name](exported_rows(data.result, visible_idx)) if report_name in BOLD_ROWS else ()
	)
	content = make_xlsx(frappe._(report_name), table, columns, widths, filters, bold_rows)
	return file_name_with_filters(report_name, filters), "xlsx", content


def exported_rows(result, visible_idx):
	"""The report rows in the order build_xlsx_data writes them (only the visible ones when the tree is folded)."""
	if not visible_idx or len(visible_idx) == len(result):
		return list(result)
	visible = set(visible_idx)
	return [row for idx, row in enumerate(result) if idx in visible]


def trial_balance_bold_rows(rows):
	"""Positions of the group accounts, the top-level heads and the total among the exported rows."""
	accounts = [row.get("account") for row in rows if isinstance(row, dict) and row.get("account")]
	groups = set(
		frappe.get_all("Account", filters={"name": ("in", accounts), "is_group": 1}, pluck="name")
		if accounts
		else []
	)
	return {
		position
		for position, row in enumerate(rows)
		if isinstance(row, dict)
		and row.get("account")
		and (row.get("account") in groups or not row.get("parent_account"))
	}


BOLD_ROWS = {"Trial Balance": trial_balance_bold_rows}


def file_name_with_filters(report_name, filters):
	"""The report name, followed by the filter values when they are included (as Frappe names it)."""
	name = report_name
	for value in (filters or {}).values():
		if isinstance(value, list):
			value = ",".join(cstr(v) for v in value)
		if value and cstr(value) not in ("Yes", "No") and len(name) + len(cstr(value)) < 200:
			name += f"_{value}"
	return name


def make_xlsx(title, table, columns, widths, filters=None, bold_rows=()):
	"""Workbook of the table (header row + rows, as build_xlsx_data makes it), typed by the report's columns;
	bold_rows: positions (0 = first row after the header) of the rows written in bold."""
	from frappe.utils.xlsxutils import get_excel_date_format
	from openpyxl import Workbook
	from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
	from openpyxl.utils import get_column_letter
	from openpyxl.workbook.child import INVALID_TITLE_REGEX

	date_format, time_format = get_excel_date_format()
	bold = Font(name="Calibri", bold=True)
	header_fill = PatternFill("solid", fgColor="D9E1F2")
	header_border = Border(bottom=Side(style="thin", color="8EA9DB"))

	workbook = Workbook()
	sheet = workbook.active
	sheet.title = INVALID_TITLE_REGEX.sub(" ", title)[:31].strip() or "Report"
	workbook.properties.creator = "BATL ERP"
	workbook.properties.title = title

	row_no = 1
	for label, value in (filters or {}).items():
		if not value:
			continue
		if isinstance(value, list):
			value = ", ".join(cstr(v) for v in value)
		sheet.cell(row_no, 1, text(label)).font = bold
		sheet.cell(row_no, 2, text(value)).data_type = "s"
		row_no += 1
	if row_no > 1:
		row_no += 1  # a blank row between the filters and the table

	header_row = row_no
	header, *rows = table
	for col_no, label in enumerate(header, 1):
		cell = sheet.cell(header_row, col_no, text(label))
		cell.data_type = "s"
		cell.font = bold
		cell.fill = header_fill
		cell.border = header_border
		cell.alignment = Alignment(vertical="center", wrap_text=True)

	fieldtypes = [column.get("fieldtype") for column in columns]
	# numbers and dates must fit their column (Excel shows ### otherwise); text keeps the report's width
	value_widths = [0] * len(header)
	for position, values in enumerate(rows):
		row_no += 1
		for col_no, value in enumerate(values, 1):
			fieldtype = fieldtypes[col_no - 1] if col_no <= len(fieldtypes) else None
			cell = sheet.cell(row_no, col_no)
			write_cell(cell, value, fieldtype, date_format, time_format)
			if position in bold_rows:
				cell.font = bold
			if col_no <= len(value_widths):
				value_widths[col_no - 1] = max(
					value_widths[col_no - 1], shown_width(cell.value, position in bold_rows)
				)

	last_row = max(row_no, header_row)
	for col_no, label in enumerate(header, 1):
		width = widths[col_no - 1] if col_no <= len(widths) else 0
		sheet.column_dimensions[get_column_letter(col_no)].width = min(
			max(width or 0, len(cstr(label)) + 2, value_widths[col_no - 1], 8), 60
		)
	sheet.freeze_panes = sheet.cell(header_row + 1, 1)
	if header:
		sheet.auto_filter.ref = f"A{header_row}:{get_column_letter(len(header))}{last_row}"

	output = BytesIO()
	workbook.save(output)
	return output.getvalue()


def shown_width(value, bold=False):
	"""Characters Excel needs to show a number (with thousands separators and 2 decimals) or a date."""
	if isinstance(value, bool) or value is None:
		return 0
	if isinstance(value, int | float):
		return len(f"{value:,.2f}") + (3 if bold else 2)
	if isinstance(value, date | datetime):
		return 12 if not isinstance(value, datetime) else 20
	return 0


def write_cell(cell, value, fieldtype, date_format, time_format):
	if value is None or value == "":
		return
	if isinstance(value, bool):
		cell.value = value
	elif isinstance(value, int | float):
		if isinstance(value, float) and not math.isfinite(value):
			return
		cell.value = value
		if fieldtype in ("Currency", "Float"):
			cell.number_format = AMOUNT_FORMAT
		elif fieldtype == "Int":
			cell.number_format = WHOLE_NUMBER_FORMAT
	elif isinstance(value, datetime):
		cell.value = value
		cell.number_format = f"{date_format} {time_format}"
	elif isinstance(value, date):
		cell.value = value
		cell.number_format = date_format
	else:
		cell.value = text(value)
		cell.data_type = "s"  # never a formula, even when it starts with "="


def text(value):
	"""Cell text as Frappe exports it (HTML removed), without the characters XML does not allow, within Excel's
	limit."""
	from frappe.utils.xlsxutils import ILLEGAL_CHARACTERS_RE, handle_html

	value = handle_html(cstr(value))
	return ILLEGAL_CHARACTERS_RE.sub("", value)[:EXCEL_TEXT_LIMIT]
