 
import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice as SalesInvoiceController
from fbr.api import FBRDigitalInvoicingAPI
from frappe.utils import cint
import pyqrcode
from decimal import Decimal, ROUND_HALF_UP


class SalesInvoice(SalesInvoiceController):
    def on_submit(self):
        super().on_submit()

        if not self.custom_post_to_fdi:
            return

        # Validate Further Tax Rate if required
        if self.fbr_sale_type.furthertax:
            try:
                rate = self.taxes[1].rate
            except (IndexError, AttributeError):
                rate = None
            if not rate or rate <= 0:
                frappe.throw("Please select a valid Further Tax Rate")

        data = self.get_mapped_data()
        api_log = frappe.new_doc("FDI Request Log")
        api_log.request_data = frappe.as_json(data, indent=4)
        api_log.save()

        settings = self.get_settings_item
        endpoint = ""

        end_points = {
            "production": "di_data/v1/di/postinvoicedata",
            "sandbox": "di_data/v1/di/postinvoicedata_sb"
        }

        if settings.get("environment") == "production":
            endpoint = end_points.get("production")
        elif settings.get("environment") == "sandbox":
            endpoint = end_points.get("sandbox")
        else:
            frappe.throw("Please select a valid environment")

        api = FBRDigitalInvoicingAPI(settings)
        response = None

        try:
            response = api.make_request("POST", endpoint, data)
            resdata = response.get("validationResponse", {})

            if resdata.get("status") == "Valid":
                safe_name = self.name.replace("/", "-")
                self.custom_fbr_invoice_no = response.get("invoiceNumber")
                frappe.db.set_value("Sales Invoice", self.name, "custom_fbr_invoice_no", self.custom_fbr_invoice_no)

                url = pyqrcode.create(self.custom_fbr_invoice_no)
                url.svg(frappe.get_site_path() + '/public/files/' + safe_name + '_online_qrcode.svg', scale=8)
                self.custom_qr_code = '/files/' + safe_name + '_online_qrcode.svg'
                frappe.db.set_value("Sales Invoice", self.name, "custom_qr_code", self.custom_qr_code)

                api_log.response_data = frappe.as_json(response, indent=4)
                api_log.save()
                frappe.msgprint("Invoice successfully submitted to FBR Invoice.")
            else:
                api_log.response_data = frappe.as_json(response, indent=4)
                api_log.save()
                frappe.log_error(
                    title="FBR Invoicing API Error",
                    message=frappe.as_json(response, indent=4)
                )
                frappe.throw("Error in FBR Invoicing")
        except Exception as e:
            api_log.error = frappe.as_json(str(e))
            api_log.save()
            frappe.log_error(
                title="FBR Invoicing API Exception",
                message=frappe.as_json(str(e))
            )
            frappe.throw(f"Error while submitting invoice to FBR: {str(e)}")

    def get_mapped_data(self):
        data = {}
        data["invoiceType"] = "Sale Invoice"
        data["invoiceDate"] = self.posting_date

        data["sellerNTNCNIC"] = self.get_settings_item.company_tax_id
        data["sellerBusinessName"] = self.company
        data["sellerProvince"] = self.get_settings_item.province

        data["buyerNTNCNIC"] = self.tax_id
        data["buyerBusinessName"] = self.customer_name
        data["buyerProvince"] = self.territory
        data["buyerAddress"] = self.customer_address
        data["buyerRegistrationType"] = getattr(self, "tax_registration", "") or ""
        data["invoiceRefNo"] = getattr(self, "ctpl_ref", "") or ""
        data["scenarioId"] = self.fbr_sale_type.scenarioid

        data["items"] = self.get_items()
        return data

    def get_items(self):
        settings = self.get_settings_item
        items = []

        if settings.send_single_item:
            further_tax = 0
            uom = self.get_and_set_uom(self.custom_hs_code)
            tax_amount = self.round_half_up(self.total * (self.taxes[0].rate / 100), 2)

            try:
                tax_rate = self.taxes[1].rate
                if tax_rate and tax_rate > 0:
                    further_tax = self.round_half_up(self.total * (tax_rate / 100), 2)
            except IndexError:
                further_tax = 0

            item_data_single = {
                "hsCode": self.custom_hs_code,
                "productDescription": f"{self.custom_hs_code}",
                "rate": "Exempt" if self.fbr_sale_type.tax_exempted else f"{cint(self.taxes[0].rate)}%",
                "uoM": uom,
                "quantity": self.round_half_up(self.total_qty, 2),
                "totalValues": self.round_half_up(self.total + tax_amount, 2),
                "valueSalesExcludingST": self.round_half_up(self.total, 2),
                "fixedNotifiedValueOrRetailPrice": 0,
                "salesTaxApplicable": tax_amount if tax_amount > 0 else 0,
                "salesTaxWithheldAtSource": 0,
                "extraTax": "",
                "furtherTax": further_tax if self.fbr_sale_type.furthertax else 0,
                "sroScheduleNo": getattr(self, "sroscheduleno", "") or "",
                "fedPayable": 0,
                "discount": 0,
                "saleType": self.fbr_sale_type.saletype,
                "sroItemSerialNo": getattr(self, "sroitemserialno", "") or ""
            }

            items.append(item_data_single)
            
        else:

            for item in self.items:
                further_tax = 0
                uom = self.get_and_set_uom(item.custom_hs_code)
                tax_amount = self.round_half_up(item.amount * (self.taxes[0].rate / 100), 2)

                try:
                    tax_rate = self.taxes[1].rate
                    if tax_rate and tax_rate > 0:
                        further_tax = self.round_half_up(item.amount * (tax_rate / 100), 2)
                except IndexError:
                    further_tax = 0

                item_data = {
                    "hsCode": item.custom_hs_code,
                    "productDescription": f"{item.item_code}-{item.idx}" if settings.get("make_items_unique") == 1 else item.item_code,
                    "rate": "Exempt" if self.fbr_sale_type.tax_exempted else f"{cint(self.taxes[0].rate)}%",
                    "uoM": uom,
                    "quantity": item.weight if settings.get("send_weight") else item.qty,
                    "totalValues": self.round_half_up(item.amount + tax_amount, 2),
                    "valueSalesExcludingST": self.round_half_up(item.amount, 2),
                    "fixedNotifiedValueOrRetailPrice": self.round_half_up(item.rate, 2) if self.fbr_sale_type.fixednotifiedvalueorretailprice else 0,
                    "salesTaxApplicable": tax_amount if tax_amount > 0 else 0,
                    "salesTaxWithheldAtSource": 0,
                    "extraTax": "",
                    "furtherTax": further_tax if self.fbr_sale_type.furthertax else 0,
                    "sroScheduleNo": self.sroscheduleno or "",
                    "fedPayable": 0,
                    "discount": 0,
                    "saleType": self.fbr_sale_type.saletype,
                    "sroItemSerialNo": self.sroitemserialno or ""
                }

                items.append(item_data)

        return items

    def get_and_set_uom(self, hs_code):
        hs_code_doc = frappe.new_doc("HS Code")
        if frappe.db.exists("HS Code", hs_code):
            hs_code_doc = frappe.get_doc("HS Code", hs_code)

        settings = self.get_settings_item
        api = FBRDigitalInvoicingAPI(settings)

        try:
            response = api.make_request("GET", f"/pdi/v2/HS_UOM?hs_code={hs_code}&annexure_id=3")
            if response:
                uom = response[0].get("description")
                hs_code_doc.hs_code = hs_code
                hs_code_doc.uom = uom
                hs_code_doc.save()
                return uom
        except Exception:
            return "Nos"

    @property
    def fbr_sale_type(self):
        if self.custom_fbr_sale_type:
            return frappe.get_doc("Fbr Sale Type", self.custom_fbr_sale_type)
        else:
            frappe.throw("Please select a valid Fbr Sale Type")

    def round_half_up(self, value, digits=2):
        q = Decimal(10) ** -digits
        return float(Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP))

    @property
    def get_settings_item(self):
        try:
            # Get default company
            default_company = frappe.defaults.get_global_default("company")

            if not default_company:
                frappe.throw("No default company set in Global Defaults")

            # Filter by company field
            doc_name = frappe.db.get_value(
                "Fbr Settings Item",
                {"company": default_company},
                "name"
            )

            if not doc_name:
                return None

            doc = frappe.get_doc("Fbr Settings Item", doc_name)
            return doc.as_dict()

        except frappe.DoesNotExistError:
            return None
        except Exception as e:
            frappe.log_error(f"Error fetching FBR item: {str(e)}")
            return None


        