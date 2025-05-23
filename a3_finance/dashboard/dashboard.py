

def get_dashboard_employee_links(data):
    # Append Contract and Vehicle to the Employee dashboard
    data['transactions'].append({
        'label': 'Employee Links',
        'items': ['Contract', 'Vehicle']
    })
    return data
