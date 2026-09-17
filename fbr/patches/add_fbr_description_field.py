from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "Item": [
            {
                "fieldname": "fbr_description",
                "label": "FBR Description",
                "fieldtype": "Data",
                "insert_after": "description",
            }
        ],
        "Sales Invoice Item": [
            {
                "fieldname": "fbr_description",
                "label": "FBR Description",
                "fieldtype": "Data",
                "insert_after": "description",
                "fetch_from": "item_code.fbr_description",
            }
        ],
    }

    create_custom_fields(custom_fields, update=True)
