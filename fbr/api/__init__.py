import frappe
import requests

class FBRDigitalInvoicingAPI:
    def __init__(self, settings):
        self.settings = settings
        self.base_url = self.settings.get("url")
        settings_doc = frappe.get_doc("Fbr Settings Item", self.settings.get("company_tax_id"))
        self.token = settings_doc.get_password("token")

    def init_request(self):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def make_request(self, method, endpoint, data=None):
        """Make API request to FBR with proper error handling."""
        self.init_request()

        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint

        url = f"https://gw.fbr.gov.pk{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                timeout=30
            )
        except requests.exceptions.RequestException as e:
            frappe.log_error(
                title="FBR Invoicing API Connection Error",
                message=str(e)
            )
            frappe.throw("Unable to connect to FBR Invoicing API")

        if response.status_code != 200:
            frappe.log_error(
                title="FBR Invoicing API Error",
                message=response.text
            )
            frappe.throw(f"Error in FBR Invoicing API: {response.text}")

        return response.json()
