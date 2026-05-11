import frappe
from frappe import _
from datetime import datetime, timedelta
import logging
from .api.fdms_client import FDMSClient
from .utils.helpers import should_retry_transaction, get_device_health_status

logger = logging.getLogger(__name__)


def sync_fiscal_device_status():
	"""
	Hourly task to sync fiscal device status with FDMS
	"""
	try:
		settings = frappe.get_doc("FDMS Settings") if frappe.db.exists("FDMS Settings") else None
		
		if not settings or not settings.enabled or not settings.auto_sync_devices:
			return
		
		# Get all active fiscal devices
		devices = frappe.get_list(
			"Fiscal Device",
			filters={"device_status": ["!=", "DELETED"]},
			fields=["name", "fdms_device_id"]
		)
		
		client = FDMSClient()
		
		for device_doc in devices:
			try:
				# Get status from FDMS
				response = client.get_device_status(device_doc["fdms_device_id"])
				
				# Update device record
				device = frappe.get_doc("Fiscal Device", device_doc["name"])
				device.device_status = response.get("status")
				device.last_sync = frappe.utils.now()
				device.save(ignore_permissions=True)
				
				logger.info(f"Synced device status: {device_doc['name']}")
			
			except Exception as e:
				logger.error(f"Error syncing device {device_doc['name']}: {str(e)}")
				device = frappe.get_doc("Fiscal Device", device_doc["name"])
				device.last_error = str(e)
				device.save(ignore_permissions=True)
	
	except Exception as e:
		logger.error(f"Error in sync_fiscal_device_status: {str(e)}")


def reconcile_transactions():
	"""
	Daily task to reconcile FDMS transactions
	"""
	try:
		settings = frappe.get_doc("FDMS Settings") if frappe.db.exists("FDMS Settings") else None
		
		if not settings or not settings.enabled:
			return
		
		# Get failed transactions from the last 24 hours
		failed_logs = frappe.get_list(
			"FDMS Transaction Log",
			filters={
				"transaction_type": "FAILED",
				"request_timestamp": [">=", datetime.now() - timedelta(days=1)],
			},
			fields=["name", "reference_name", "reference_doctype"]
		)
		
		for log_entry in failed_logs:
			try:
				log = frappe.get_doc("FDMS Transaction Log", log_entry["name"])
				
				# Check if we should retry
				if should_retry_transaction(log):
					# Create retry log
					retry_log = frappe.get_doc({
						"doctype": "FDMS Transaction Log",
						"reference_name": log.reference_name,
						"reference_doctype": log.reference_doctype,
						"transaction_type": "RETRY",
						"request_timestamp": frappe.utils.now(),
						"response_data": "{}",
					})
					retry_log.insert(ignore_permissions=True)
					
					logger.info(f"Scheduled retry for {log.reference_name}")
			
			except Exception as e:
				logger.error(f"Error reconciling transaction {log_entry['name']}: {str(e)}")
	
	except Exception as e:
		logger.error(f"Error in reconcile_transactions: {str(e)}")


def generate_compliance_report():
	"""
	Daily task to generate compliance report
	"""
	try:
		settings = frappe.get_doc("FDMS Settings") if frappe.db.exists("FDMS Settings") else None
		
		if not settings or not settings.enabled or not settings.generate_compliance_reports:
			return
		
		# Get report date range
		today = datetime.now().date()
		start_date = (today - timedelta(days=1)).isoformat()
		end_date = today.isoformat()
		
		# Get fiscalised invoices
		fiscalised_invoices = frappe.get_list(
			"Sales Invoice",
			filters={
				"posting_date": [">=", start_date],
				"posting_date": ["<=", end_date],
				"fiscal_status": "FISCALISED",
				"docstatus": 1,
			},
			fields=["name", "posting_date", "total", "fiscal_code"],
		)
		
		if not fiscalised_invoices:
			logger.info("No fiscalised invoices for today")
			return
		
		# Create compliance report
		total_amount = sum(inv.get("total", 0) for inv in fiscalised_invoices)
		
		report_doc = frappe.get_doc({
			"doctype": "Compliance Report",
			"report_date": today,
			"start_date": start_date,
			"end_date": end_date,
			"invoices_count": len(fiscalised_invoices),
			"total_amount": total_amount,
			"currency": "ZWL",
		})
		
		report_doc.insert(ignore_permissions=True)
		logger.info(f"Generated compliance report for {today}")
	
	except Exception as e:
		logger.error(f"Error in generate_compliance_report: {str(e)}")


def check_device_health():
	"""
	Check health status of all fiscal devices (can be called manually or scheduled)
	"""
	try:
		devices = frappe.get_list(
			"Fiscal Device",
			filters={"device_status": ["!=", "DELETED"]},
			fields=["name"]
		)
		
		health_statuses = {}
		
		for device_doc in devices:
			try:
				health = get_device_health_status(device_doc["name"])
				health_statuses[device_doc["name"]] = health
				
				# Alert if device is in critical state
				if health.get("health") == "CRITICAL":
					frappe.log_error(
						f"Fiscal Device {device_doc['name']} is in CRITICAL state",
						"Device Health Alert"
					)
			
			except Exception as e:
				logger.error(f"Error checking device health: {str(e)}")
		
		return health_statuses
	
	except Exception as e:
		logger.error(f"Error in check_device_health: {str(e)}")
		return {}
