# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, getdate
from frappe import msgprint, _
from calendar import monthrange

status_map = {
	"Absent": "A",
	"Half Day": "HD",
	"Holiday": "<b>H</b>",
	"Weekly Off": "<b>WO</b>",
	"On Leave": "L",
	"Present": "P",
	"Work From Home": "WFH"
	}

day_abbr = [
	"Mon",
	"Tue",
	"Wed",
	"Thu",
	"Fri",
	"Sat",
	"Sun"
]

def execute(filters=None):
	if not filters: filters = {}

	if filters.hide_year_field == 1:
		filters.year = 2020

	conditions, filters = get_conditions(filters)
	columns, days = get_columns(filters)
	att_map = get_attendance_list(conditions, filters)

	if filters.group_by:
		emp_map, group_by_parameters = get_employee_details(filters.group_by, filters.company)
		holiday_list = []
		for parameter in group_by_parameters:
			h_list = [emp_map[parameter][d]["holiday_list"] for d in emp_map[parameter] if emp_map[parameter][d]["holiday_list"]]
			holiday_list += h_list
	else:
		emp_map = get_employee_details(filters.group_by, filters.company)
		holiday_list = [emp_map[d]["holiday_list"] for d in emp_map if emp_map[d]["holiday_list"]]


	default_holiday_list = frappe.get_cached_value('Company',  filters.get("company"),  "default_holiday_list")
	holiday_list.append(default_holiday_list)
	holiday_list = list(set(holiday_list))
	holiday_map = get_holiday(holiday_list, filters["month"])

	data = []

	leave_list = None
	if filters.summarized_view:
		leave_types = frappe.db.sql("""select name from `tabLeave Type`""", as_list=True)
		leave_list = [d[0] + ":Float:120" for d in leave_types]
		columns.extend(leave_list)
		columns.extend([_("Total Late Entries") + ":Float:120", _("Total Early Exits") + ":Float:120"])

	if filters.group_by:
		emp_att_map = {}
		for parameter in group_by_parameters:
			data.append([ "<b>"+ parameter + "</b>"])
			record, aaa = add_data(emp_map[parameter], att_map, filters, holiday_map, conditions, default_holiday_list, leave_list=leave_list)
			emp_att_map.update(aaa)
			data += record
	else:
		record, emp_att_map = add_data(emp_map, att_map, filters, holiday_map, conditions, default_holiday_list, leave_list=leave_list)
		data += record

	chart_data = get_chart_data(emp_att_map, days)

	return columns, data, None, chart_data

def get_chart_data(emp_att_map, days):
	labels = []
	datasets = [
		{"name": "Absent", "values": []},
		{"name": "Present", "values": []},
		{"name": "Leave", "values": []},
	]
	for idx, day in enumerate(days, start=0):
		p = day.replace("::65", "")
		labels.append(day.replace("::65", ""))
		total_absent_on_day = 0
		total_leave_on_day = 0
		total_present_on_day = 0
		total_holiday = 0
		for emp in emp_att_map.keys():
			if emp_att_map[emp][idx]:
				if emp_att_map[emp][idx] == "A":
					total_absent_on_day += 1
				if emp_att_map[emp][idx] in ["P", "WFH"]:
					total_present_on_day += 1
				if emp_att_map[emp][idx] == "HD":
					total_present_on_day += 0.5
					total_leave_on_day += 0.5
				if emp_att_map[emp][idx] == "L":
					total_leave_on_day += 1


		datasets[0]["values"].append(total_absent_on_day)
		datasets[1]["values"].append(total_present_on_day)
		datasets[2]["values"].append(total_leave_on_day)


	chart = {
		"data": {
			'labels': labels,
			'datasets': datasets
		}
	}

	chart["type"] = "line"

	return chart

def add_data(employee_map, att_map, filters, holiday_map, conditions, default_holiday_list, leave_list=None):

	record = []
	emp_att_map = {}
	for emp in employee_map:
		print("------------emp",emp)
		emp_det = employee_map.get(emp)
		if not emp_det or emp not in att_map:
			continue

		row = []
		if filters.group_by:
			row += [" "]
		row += [emp, emp_det.employee_name]

		total_p = total_a = total_l = total_h = total_um= 0.0
		emp_status_map = []
		for day in range(filters["total_days_in_month"]):
			status = None
			status = att_map.get(emp).get(day + 1)
			if status is None and holiday_map:
				emp_holiday_list = emp_det.holiday_list if emp_det.holiday_list else default_holiday_list

				if emp_holiday_list in holiday_map:
					for idx, ele in enumerate(holiday_map[emp_holiday_list]):
						if day+1 == holiday_map[emp_holiday_list][idx][0]:
							if holiday_map[emp_holiday_list][idx][1]:
								status = "Weekly Off"
							else:
								status = "Holiday"
							total_h += 1
			abbr = status_map.get(status, "")
			if abbr not in ['<b>H</b>','L','<b>WO</b>']:
				print("---------filters.get('employee')",emp)
				attendance_date = filters.get('year') + "-" + filters.get('month') + "-" + str(day + 1)
				att_detail = frappe.db.sql("""select * from `tabAttendance` where attendance_date =%s and 
							employee = %s and company = %s limit 1""",(attendance_date, emp, filters.get('company')),as_dict=True)
				if att_detail:
					check_in_lst = None
					check_in_time = ''
					check_in = frappe.db.sql("""select * from `tabEmployee Checkin` where attendance = %s order by time limit 1""",att_detail[0].name,as_dict=True)
					if check_in:
						if check_in[0].time:
							check_in_lst = check_in[0].name
							check_in_time = (check_in[0].time).time()
							check_in_time = str(check_in_time.strftime("%H:%M"))
					check_out_time = ''
					check_out_query = """select * from `tabEmployee Checkin` where attendance = '{0}'""".format(att_detail[0].name)
					if check_in_lst:
						check_out_query += """ and name != '{0}'""".format(check_in_lst)
					check_out = frappe.db.sql(check_out_query,as_dict=True)
					if check_out:
						if check_out[0].time:
							check_out_time = (check_out[0].time).time()
							check_out_time = str(check_out_time.strftime("%H:%M"))

					working_hour = (str(round(att_detail[0].working_hours,1)) if att_detail[0].working_hours else str(0))
					full_str = "(" + check_in_time + " - " + check_out_time+")" + working_hour
					emp_status_map.append(full_str)
				else:
					emp_status_map.append(" ")
					# emp_status_map.append(abbr)
			else:
				emp_status_map.append(abbr)

			if filters.summarized_view:
				if status == "Present" or status == "Work From Home":
					total_p += 1
				elif status == "Absent":
					total_a += 1
				elif status == "On Leave":
					total_l += 1
				elif status == "Half Day":
					total_p += 0.5
					total_a += 0.5
					total_l += 0.5
				elif not status:
					total_um += 1

		if not filters.summarized_view:
			row += emp_status_map

		if filters.summarized_view:
			row += [total_p, total_l, total_a, total_h, total_um]

		if not filters.get("employee"):
			filters.update({"employee": emp})
			conditions += " and employee = %(employee)s"
		elif not filters.get("employee") == emp:
			filters.update({"employee": emp})

		if filters.summarized_view:
			leave_details = frappe.db.sql("""select leave_type, status, count(*) as count from `tabAttendance`\
				where leave_type is not NULL %s group by leave_type, status""" % conditions, filters, as_dict=1)

			time_default_counts = frappe.db.sql("""select (select count(*) from `tabAttendance` where \
				late_entry = 1 %s) as late_entry_count, (select count(*) from tabAttendance where \
				early_exit = 1 %s) as early_exit_count""" % (conditions, conditions), filters)

			leaves = {}
			for d in leave_details:
				if d.status == "Half Day":
					d.count = d.count * 0.5
				if d.leave_type in leaves:
					leaves[d.leave_type] += d.count
				else:
					leaves[d.leave_type] = d.count

			for d in leave_list:
				if d in leaves:
					row.append(leaves[d])
				else:
					row.append("0.0")

			row.extend([time_default_counts[0][0],time_default_counts[0][1]])
		emp_att_map[emp] = emp_status_map
		record.append(row)

	return record, emp_att_map

def get_columns(filters):

	columns = []

	if filters.group_by:
		columns = [_(filters.group_by)+ ":Link/Branch:120"]

	columns += [
		_("Employee") + ":Link/Employee:120", _("Employee Name") + ":Data/:120"
	]
	days = []
	for day in range(filters["total_days_in_month"]):
		date = str(filters.year) + "-" + str(filters.month)+ "-" + str(day+1)
		day_name = day_abbr[getdate(date).weekday()]
		days.append(cstr(day+1)+ " " +day_name +"::120")
	if not filters.summarized_view:
		columns += days

	if filters.summarized_view:
		columns += [_("Total Present") + ":Float:120", _("Total Leaves") + ":Float:120",  _("Total Absent") + ":Float:120", _("Total Holidays") + ":Float:120", _("Unmarked Days")+ ":Float:120"]
	return columns, days

def get_attendance_list(conditions, filters):
	attendance_list = frappe.db.sql("""select employee, day(attendance_date) as day_of_month,
		status from tabAttendance where docstatus = 1 %s order by employee, attendance_date""" %
		conditions, filters, as_dict=1)

	att_map = {}
	for d in attendance_list:
		att_map.setdefault(d.employee, frappe._dict()).setdefault(d.day_of_month, "")
		att_map[d.employee][d.day_of_month] = d.status

	return att_map

def get_conditions(filters):
	if not (filters.get("month") and filters.get("year")):
		msgprint(_("Please select month and year"), raise_exception=1)

	filters["total_days_in_month"] = monthrange(cint(filters.year), cint(filters.month))[1]

	conditions = " and month(attendance_date) = %(month)s and year(attendance_date) = %(year)s"

	if filters.get("company"): conditions += " and company = %(company)s"
	if filters.get("employee"): conditions += " and employee = %(employee)s"

	return conditions, filters

def get_employee_details(group_by, company):
	emp_map = {}
	query = """select name, employee_name, designation, department, branch, company,
		holiday_list from `tabEmployee` where company = %s """ % frappe.db.escape(company)

	if group_by:
		group_by = group_by.lower()
		query += " order by " + group_by + " ASC"

	employee_details = frappe.db.sql(query , as_dict=1)

	group_by_parameters = []
	if group_by:

		group_by_parameters = list(set(detail.get(group_by, "") for detail in employee_details if detail.get(group_by, "")))
		for parameter in group_by_parameters:
				emp_map[parameter] = {}


	for d in employee_details:
		if group_by and len(group_by_parameters):
			if d.get(group_by, None):

				emp_map[d.get(group_by)][d.name] = d
		else:
			emp_map[d.name] = d

	if not group_by:
		return emp_map
	else:
		return emp_map, group_by_parameters

def get_holiday(holiday_list, month):
	holiday_map = frappe._dict()
	for d in holiday_list:
		if d:
			holiday_map.setdefault(d, frappe.db.sql('''select day(holiday_date), weekly_off from `tabHoliday`
				where parent=%s and month(holiday_date)=%s''', (d, month)))

	return holiday_map

@frappe.whitelist()
def get_attendance_years():
	year_list = frappe.db.sql_list("""select distinct YEAR(attendance_date) from tabAttendance ORDER BY YEAR(attendance_date) DESC""")
	if not year_list:
		year_list = [getdate().year]

	return "\n".join(str(year) for year in year_list)
