import frappe
import requests



class FBRDigitalInvoicingAPI:
    def __init__(self,settings):
        self.settings = settings
        self.base_url = settings.get("url")
        settings_doc = frappe.get_doc("Fbr Settings Item", self.settings.get("company_tax_id"))
        self.token = settings_doc.get_password("token")
       
    def init_request(self):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)


    def make_request(self, method, endpint, data=None):
        self.init_request()
        frappe.log_error(
            title="Checking urls",
            message=f"Request: {method} {self.base_url}/{endpint} {data}"
        )
        request = self.session.request(method, f"{self.base_url}/{endpint}", json=data)
        if request.status_code != 200:
            
            frappe.log_error(
                title="FBR Invoicing API Error",
                message=f"Error in FBR Invoicing API: {request.text}"
            )
            frappe.throw(f"Error in FBR Invoicing API: {request.text}")
        return request.json()

