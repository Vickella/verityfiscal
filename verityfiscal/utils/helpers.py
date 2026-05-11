import frappe
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime, timedelta
import hashlib
import hmac

logger = logging.getLogger(__name__)


def encrypt_sensitive_data(data: str, key: str = None) -> str:
	"""
	Encrypt sensitive data (API keys, etc.)

	Args:
		data: Data to encrypt
		key: Encryption key (uses app secret if not provided)

	Returns:
		Encrypted string (base64 encoded)
	"""
	from cryptography.fernet import Fernet
	import base64

	if not key:
		key = frappe.conf.get("encryption_key", frappe.conf.get("secret_key"))
	
	# Derive a key from the secret
	derived_key = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
	cipher = Fernet(derived_key)
	
	encrypted = cipher.encrypt(data.encode())
	return encrypted.decode()


def decrypt_sensitive_data(encrypted_data: str, key: str = None) -> str:
	"""
	Decrypt sensitive data

	Args:
		encrypted_data: Encrypted data string
		key: Encryption key (uses app secret if not provided)

	Returns:
		Decrypted string
	"""
	from cryptography.fernet import Fernet
	import base64

	if not key:
		key = frappe.conf.get("encryption_key", frappe.conf.get("secret_key"))
	
	# Derive a key from the secret
	derived_key = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
	cipher = Fernet(derived_key)
	
	decrypted = cipher.decrypt(encrypted_data.encode())
	return decrypted.decode()


def validate_tin(tin: str) -> bool:
	"""
	Validate Zimbabwe Tax Identification Number format

	Args:
		tin: TIN string

	Returns:
		True if valid, False otherwise
	"""
	if not tin or not isinstance(tin, str):
		return False
	
	# Zimbabwe TIN format: 10 digits
	if len(tin) != 10 or not tin.isdigit():
		return False
	
	return True


def validate_invoice_data(invoice_data: Dict[str, Any]) -> tuple[bool, str]:
	"""
	Validate invoice data before sending to FDMS

	Args:
		invoice_data: Invoice data dictionary

	Returns:
		Tuple of (is_valid, error_message)
	"""
	required_fields = ['invoice_number', 'invoice_date', 'customer_name', 'total_amount']
	
	# Check required fields
	for field in required_fields:
		if not invoice_data.get(field):
			return False, f"Missing required field: {field}"
	
	# Validate total amount
	try:
		total = float(invoice_data.get('total_amount', 0))
		if total < 0:
			return False, "Total amount cannot be negative"
	except (ValueError, TypeError):
		return False, "Invalid total amount"
	
	# Validate items
	items = invoice_data.get('items', [])
	if not items:
		return False, "Invoice must have at least one item"
	
	for idx, item in enumerate(items):
		if not item.get('description'):
			return False, f"Item {idx + 1} missing description"
		if not item.get('quantity') or float(item.get('quantity', 0)) <= 0:
			return False, f"Item {idx + 1} has invalid quantity"
		if not item.get('unit_price') or float(item.get('unit_price', 0)) < 0:
			return False, f"Item {idx + 1} has invalid unit price"
	
	return True, ""


def format_invoice_for_qr(invoice_data: Dict[str, Any]) -> str:
	"""
	Format invoice data for QR code generation

	Args:
		invoice_data: Invoice data dictionary

	Returns:
		Formatted QR code string
	"""
	qr_data = {
		"in": invoice_data.get("invoice_number"),
		"id": invoice_data.get("fiscal_code"),
		"tc": invoice_data.get("total_amount"),
		"t": invoice_data.get("tax_amount", 0),
	}
	
	return json.dumps(qr_data)


def generate_qr_code(data: str) -> Optional[str]:
	"""
	Generate QR code from data

	Args:
		data: Data to encode in QR code

	Returns:
		QR code image as base64 string or None
	"""
	try:
		import qrcode
		import io
		import base64
		
		qr = qrcode.QRCode(version=1, box_size=10, border=5)
		qr.add_data(data)
		qr.make(fit=True)
		
		img = qr.make_image(fill_color="black", back_color="white")
		
		# Convert to base64
		buffer = io.BytesIO()
		img.save(buffer, format="PNG")
		img_str = base64.b64encode(buffer.getvalue()).decode()
		
		return f"data:image/png;base64,{img_str}"
	
	except ImportError:
		logger.warning("qrcode library not installed")
		return None
	except Exception as e:
		logger.error(f"Error generating QR code: {str(e)}")
		return None


def get_invoice_items_summary(invoice_data: Dict[str, Any]) -> str:
	"""
	Get a summary of invoice items for logging

	Args:
		invoice_data: Invoice data dictionary

	Returns:
		Summary string
	"""
	items = invoice_data.get('items', [])
	if not items:
		return "No items"
	
	summary_items = []
	for item in items[:3]:  # Show first 3 items
		summary_items.append(f"{item.get('description')} (x{item.get('quantity')})")
	
	if len(items) > 3:
		summary_items.append(f"and {len(items) - 3} more items")
	
	return ", ".join(summary_items)


def should_retry_transaction(transaction_log_doc) -> bool:
	"""
	Determine if a transaction should be retried

	Args:
		transaction_log_doc: FDMS Transaction Log document

	Returns:
		True if should retry, False otherwise
	"""
	if transaction_log_doc.transaction_type != "FAILED":
		return False
	
	settings = frappe.get_doc("FDMS Settings") if frappe.db.exists("FDMS Settings") else None
	if not settings or not settings.retry_failed_transmissions:
		return False
	
	# Get retry count for this transaction
	retry_count = frappe.db.count(
		"FDMS Transaction Log",
		filters={
			"reference_name": transaction_log_doc.reference_name,
			"transaction_type": "RETRY",
		}
	)
	
	max_retries = settings.retry_attempts if settings else 3
	
	return retry_count < max_retries


def schedule_transaction_retry(transaction_log_name: str, delay_seconds: int = None):
	"""
	Schedule a transaction for retry

	Args:
		transaction_log_name: Name of the FDMS Transaction Log
		delay_seconds: Delay before retry in seconds
	"""
	settings = frappe.get_doc("FDMS Settings") if frappe.db.exists("FDMS Settings") else None
	delay = delay_seconds or (settings.retry_interval if settings else 300)
	
	retry_time = datetime.now() + timedelta(seconds=delay)
	
	# Schedule job
	frappe.enqueue(
		"verityfiscal.utils.helpers.execute_transaction_retry",
		transaction_log_name=transaction_log_name,
		at_time=retry_time,
	)


def execute_transaction_retry(transaction_log_name: str):
	"""
	Execute a scheduled transaction retry

	Args:
		transaction_log_name: Name of the FDMS Transaction Log
	"""
	transaction_log = frappe.get_doc("FDMS Transaction Log", transaction_log_name)
	
	reference_doc = frappe.get_doc(
		transaction_log.reference_doctype,
		transaction_log.reference_name
	)
	
	if transaction_log.reference_doctype == "Sales Invoice":
		from verityfiscal.api.invoice import send_invoice_to_fdms
		send_invoice_to_fdms(reference_doc.name)


def get_fiscal_device_for_location(location: str) -> Optional[str]:
	"""
	Get the default fiscal device for a location

	Args:
		location: Location name or code

	Returns:
		Fiscal Device name or None
	"""
	device = frappe.db.get_value(
		"Fiscal Device",
		{"location": location, "device_status": "ACTIVE"},
		"name"
	)
	return device


def export_compliance_report(start_date: str, end_date: str) -> Dict[str, Any]:
	"""
	Export compliance report for a date range

	Args:
		start_date: Start date (ISO format)
		end_date: End date (ISO format)

	Returns:
		Compliance report data
	"""
	try:
		# Get fiscalised invoices
		fiscalised_invoices = frappe.get_list(
			"Sales Invoice",
			filters={
				"posting_date": [">=", start_date],
				"posting_date": ["<=", end_date],
				"fiscal_status": "FISCALISED",
			},
			fields=["name", "posting_date", "total", "fiscal_code"],
		)
		
		# Get transaction logs
		transaction_logs = frappe.get_list(
			"FDMS Transaction Log",
			filters={
				"request_timestamp": [">=", start_date],
				"request_timestamp": ["<=", end_date],
			},
			fields=["name", "transaction_type", "reference_name"],
		)
		
		return {
			"start_date": start_date,
			"end_date": end_date,
			"fiscalised_count": len(fiscalised_invoices),
			"total_amount": sum(inv.get("total", 0) for inv in fiscalised_invoices),
			"transaction_logs_count": len(transaction_logs),
			"invoices": fiscalised_invoices,
			"transactions": transaction_logs,
		}
	
	except Exception as e:
		logger.error(f"Error generating compliance report: {str(e)}")
		return {}


def get_device_health_status(fiscal_device_name: str) -> Dict[str, Any]:
	"""
	Get health status of a fiscal device

	Args:
		fiscal_device_name: Name of the Fiscal Device

	Returns:
		Health status information
	"""
	try:
		device = frappe.get_doc("Fiscal Device", fiscal_device_name)
		
		# Get recent transaction count
		recent_count = frappe.db.count(
			"FDMS Transaction Log",
			filters={
				"reference_name": ["like", f"%{fiscal_device_name}%"],
				"request_timestamp": [">=", datetime.now() - timedelta(days=7)],
			}
		)
		
		# Get failure rate
		failed_count = frappe.db.count(
			"FDMS Transaction Log",
			filters={
				"reference_name": ["like", f"%{fiscal_device_name}%"],
				"transaction_type": "FAILED",
				"request_timestamp": [">=", datetime.now() - timedelta(days=7)],
			}
		)
		
		failure_rate = (failed_count / recent_count * 100) if recent_count > 0 else 0
		
		return {
			"device_name": device.name,
			"device_status": device.device_status,
			"last_sync": device.last_sync,
			"recent_transactions": recent_count,
			"failed_transactions": failed_count,
			"failure_rate": failure_rate,
			"health": "HEALTHY" if failure_rate < 5 else "WARNING" if failure_rate < 10 else "CRITICAL",
		}
	
	except Exception as e:
		logger.error(f"Error getting device health: {str(e)}")
		return {}
