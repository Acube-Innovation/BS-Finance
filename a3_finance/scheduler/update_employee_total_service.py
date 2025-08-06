import frappe
from datetime import datetime

def update_total_service_for_all_employees():
    today = datetime.today().date()
    print("✅ Service updater started on:", today)

    # Uncomment this in production
    # if today.day != 1:
    #     print("❌ Not the first day of the month. Skipping...")
    #     return

    employees = frappe.get_all(
        "Employee",
        filters={"date_of_joining": ["is", "set"]},
        fields=["name", "employee_name", "date_of_joining"]
    )

    print(f"🔍 Found {len(employees)} employee(s) with date_of_joining.")

    updated_count = 0

    for emp in employees:
        doj = emp.date_of_joining
        if not doj:
            print(f"⚠️ Skipping {emp.name} - No date_of_joining")
            continue

        if doj > today:
            print(f"⚠️ Skipping {emp.name} - Future joining date: {doj}")
            continue

        years = today.year - doj.year
        months = today.month - doj.month

        if months < 0:
            years -= 1
            months += 12

        # Format both parts, even if zero
        service_str = f"{years} Year{'s' if years != 1 else ''} and {months} Month{'s' if months != 1 else ''}"

        print(f"📝 Updating {emp.employee_name} ({emp.name}) — Joined: {doj} → Service: {service_str}")

        frappe.db.set_value("Employee", emp.name, "custom_total_service", service_str)
        updated_count += 1

    frappe.db.commit()
    print(f"✅ Updated total_service for {updated_count} employee(s).")
