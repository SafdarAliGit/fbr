import frappe
import requests


class FBRDigitalInvoicingAPI:
    def __init__(self, settings):
        self.settings = settings
        self.base_url = self.settings.get("url")

        # Fetch token safely
        settings_doc = frappe.get_doc(
            "Fbr Settings Item",
            self.settings.get("company_tax_id")
        )
        self.token = settings_doc.get_password("token")

        # Initialize session once
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        })

    def make_request(self, method, endpoint, data=None):
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                timeout=30
            )
        except requests.exceptions.RequestException as e:
            frappe.log_error(
                title="FBR API Connection Error",
                message=str(e)
            )
            frappe.throw("Unable to connect to FBR API")

        # Accept all successful HTTP codes
        if not response.ok:
            frappe.log_error(
                title="FBR Invoicing API Error",
                message=response.text
            )
            frappe.throw(f"Error in FBR Invoicing API: {response.text}")

        # Some responses may not return JSON
        try:
            return response.json()
        except ValueError:
            return response.text
