import frappe
import requests



class FBRDigitalInvoicingAPI:
    def __init__(self,settings):
        self.settings = settings
        frappe.error_log("TEST ERROR", f"url: {settings.get('url')}, token: {settings.get('token')}, environment: {settings.get('environment')}, company_tax_id: {settings.get('company_tax_id')}")
        self.base_url = settings.get("url")
        self.token = settings.get("token")
        frappe.log_error(
            title="FBR Invoicing API Error",
            message=f"Error in FBR Invoicing API: {settings}"
        )   
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

