import frappe
import requests



class FBRDigitalInvoicingAPI:
    def __init__(self,settings):
        self.settings = settings
        self.base_url = settings.get("url")
        self.token = settings.get("token")

    def init_request(self):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)


    def make_request(self, method, endpint, data=None):
        self.init_request()
        request = self.session.request(method, f"{self.base_url}/{endpint}", json=data)
        if request.status_code != 200:
            
            frappe.log_error(
                title="FBR Invoicing API Error",
                message=f"Error in FBR Invoicing API: {request.text}"
            )
            frappe.throw(f"Error in FBR Invoicing API: {request.text}")
        return request.json()

    @property
    def get_settings_item(self):
        """Get single row by company_tax_id"""
        try:
            row = frappe.db.get_value(
                "Fbr Settings Item",
                {"company_tax_id": self.company_tax_id},
                ["*"],
                as_dict=True
            )
            return row
        except frappe.DoesNotExistError:
            return None
        except Exception as e:
            frappe.log_error(f"Error fetching FBR item: {str(e)}")
            return None 