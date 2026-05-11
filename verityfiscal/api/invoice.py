import frappe
from frappe import _
from typing import Dict, Any
from .fdms_client import FDMSClient, FDMSException
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@frappe.whitelist()
def send_invoice_to_fdms(invoice_name: str) -> Dict[str, Any]:
	"""
	Send a Sales Invoice to FDMS for fiscalisation

	Args:
		invoice_name: Name of the Sales Invoice

	Returns:
		Dictionary with fiscalisation result
	"""
	try:
		invoice = frappe.get_doc("Sales Invoice", invoice_name)
		
		# Check if invoice is valid for fiscalisation
		if not invoice.docstatus == 1:
			return {"status": "error", "message": _("Invoice must be submitted")}
		
		# Check FDMS settings
		settings = frappe.get_doc("FDMS Settings") if frappe.db.exists("FDMS Settings") else None
		if not settings or not settings.enabled:
			return {"status": "error", "message": _("FDMS is not enabled or not configured")}
		
		# Get fiscal device
		fiscal_device = frappe.get_doc("Fiscal Device", invoice.fiscal_device)
		if not fiscal_device:
			return {"status": "error", "message": _("Fiscal device not found")}
		
		# Prepare invoice data
		invoice_data = _prepare_invoice_data(invoice, fiscal_device)
		
		# Send to FDMS
		client = FDMSClient()
		response = client.send_invoice(invoice_data)
		
		# Save fiscalisation details
		invoice.fiscal_code = response.get("fiscal_code")
		invoice.qr_code = response.get("qr_code")
		invoice.fdms_reference = response.get("reference_code")
		invoice.fiscal_status = "FISCALISED"
		invoice.fiscalisation_date = datetime.now()
		invoice.db_update()
		
		# Create FDMS Transaction log
		create_transaction_log(
			invoice_name,
			"Sales Invoice",
			"FISCALISED",
			response
		)
		
		frappe.msgprint(_("Invoice successfully fiscalised"), alert=True)
		
		return {
			"status": "success",
			"message": _("Invoice fiscalised successfully"),
			"fiscal_code": response.get("fiscal_code"),
			"qr_code": response.get("qr_code"),
		}
	
	except FDMSException as e:
		logger.error(f"FDMS error: {str(e)}")
		create_transaction_log(invoice_name, "Sales Invoice", "FAILED", {"error": str(e)})
		return {"status": "error", "message": str(e)}
	except Exception as e:
		logger.error(f"Unexpected error: {str(e)}")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_invoice_fiscalisation_status(invoice_name: str) -> Dict[str, Any]:
	"""
	Get the fiscalisation status of an invoice

	Args:
		invoice_name: Name of the Sales Invoice

	Returns:
		Dictionary with fiscal status
	"""
	try:
		invoice = frappe.get_doc("Sales Invoice", invoice_name)
		
		if not invoice.fiscal_code:
			return {
				"status": "pending",
				"message": _("Invoice not yet fiscalised")
			}
		
		# Check with FDMS
		client = FDMSClient()
		response = client.get_invoice_status(invoice.fiscal_code)
		
		return {
			"status": response.get("status"),
			"message": response.get("message"),
			"fiscal_code": invoice.fiscal_code,
			"fiscalisation_date": invoice.fiscalisation_date,
		}
	
	except Exception as e:
		logger.error(f"Error fetching status: {str(e)}")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def resend_failed_invoice(invoice_name: str) -> Dict[str, Any]:
	"""
	Retry sending a failed invoice

	Args:
		invoice_name: Name of the Sales Invoice

	Returns:
		Dictionary with result
	"""
	try:
		invoice = frappe.get_doc("Sales Invoice", invoice_name)
		
		if invoice.fiscal_status == "FISCALISED":
			return {
				"status": "info",
				"message": _("Invoice is already fiscalised")
			}
		
		# Send to FDMS
		return send_invoice_to_fdms(invoice_name)
	
	except Exception as e:
		logger.error(f"Error resending invoice: {str(e)}")
		return {"status": "error", "message": str(e)}


def on_sales_invoice_submit(doc, method):
	"""
	Hook to automatically fiscalise sales invoices on submit
	"""
	settings = frappe.get_doc("FDMS Settings") if frappe.db.exists("FDMS Settings") else None
	
	if not settings or not settings.auto_fiscalise:
		return
	
	# Auto-fiscalise invoice
	try:
		result = send_invoice_to_fdms(doc.name)
		if result["status"] != "success":
			frappe.throw(_("Failed to fiscalise invoice: {0}").format(result["message"]))
	except Exception as e:
		frappe.throw(_("Error during fiscalisation: {0}").format(str(e)))


def on_sales_invoice_cancel(doc, method):
	"""
	Handle cancellation of fiscalised invoices
	"""
	if doc.fiscal_status == "FISCALISED":
		# Log the cancellation
		create_transaction_log(
			doc.name,
			"Sales Invoice",
			"CANCELLED",
			{"previous_fiscal_code": doc.fiscal_code}
		)
		
		frappe.msgprint(_("Note: Fiscal record has been logged but not deleted from FDMS"))


def on_purchase_invoice_submit(doc, method):
	"""
	Handle purchase invoices - log for compliance
	"""
	create_transaction_log(
		doc.name,
		"Purchase Invoice",
		"SUBMITTED",
		{"invoice_number": doc.name}
	)


def _prepare_invoice_data(invoice, fiscal_device) -> Dict[str, Any]:
	"""
	Prepare invoice data for FDMS transmission

	Args:
		invoice: Sales Invoice document
		fiscal_device: Fiscal Device document

	Returns:
		Formatted invoice data
	"""
	items = []
	for item in invoice.items:
		items.append({
			"description": item.item_name,
			"quantity": item.qty,
			"unit_price": item.rate,
			"amount": item.amount,
			"tax_rate": item.tax_rate if hasattr(item, 'tax_rate') else 0,
		})
	
	return {
		"invoice_number": invoice.name,
		"invoice_date": invoice.posting_date.isoformat(),
		"invoice_type": "REGULAR",
		"customer_tin": invoice.customer_tax_id if hasattr(invoice, 'customer_tax_id') else None,
		"customer_name": invoice.customer_name,
		"items": items,
		"subtotal": invoice.total - invoice.total_taxes_and_charges,
		"tax_amount": invoice.total_taxes_and_charges,
		"total_amount": invoice.total,
		"currency": invoice.currency,
		"device_id": fiscal_device.fdms_device_id,
		"reference_code": invoice.name,
	}


def create_transaction_log(
	reference_name: str,
	reference_doctype: str,
	transaction_type: str,
	response_data: Dict[str, Any]
):
	"""
	Create a log entry for FDMS transactions

	Args:
		reference_name: Name of the reference document
		reference_doctype: Doctype of the reference document
		transaction_type: Type of transaction (FISCALISED, FAILED, etc.)
		response_data: Response data from FDMS or error details
	"""
	try:
		log = frappe.get_doc({
			"doctype": "FDMS Transaction Log",
			"reference_name": reference_name,
			"reference_doctype": reference_doctype,
			"transaction_type": transaction_type,
			"request_timestamp": datetime.now(),
			"response_data": json.dumps(response_data),
		})
		log.insert(ignore_permissions=True)
	except Exception as e:
		logger.error(f"Failed to create transaction log: {str(e)}")
