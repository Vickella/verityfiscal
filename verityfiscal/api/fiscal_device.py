import frappe
from frappe import _
from typing import Dict, Any, List
from .fdms_client import FDMSClient, FDMSException
import logging

logger = logging.getLogger(__name__)


@frappe.whitelist()
def register_fiscal_device(device_data: Dict[str, Any]) -> Dict[str, Any]:
	"""
	Register a new fiscal device with FDMS

	Args:
		device_data: Dictionary containing:
			- device_name: Device name
			- device_type: Type of device
			- serial_number: Device serial number
			- taxpayer_tin: Taxpayer TIN
			- location: Device location
			- activation_key: Activation key (if available)

	Returns:
		Dictionary with registration result
	"""
	try:
		# Validate required fields
		required_fields = ['device_type', 'serial_number', 'taxpayer_tin']
		for field in required_fields:
			if not device_data.get(field):
				return {"status": "error", "message": _(f"Missing required field: {field}")}
		
		# Check if device already exists
		existing = frappe.db.get_value(
			"Fiscal Device",
			{"serial_number": device_data.get("serial_number")}
		)
		if existing:
			return {
				"status": "error",
				"message": _("Device with this serial number already exists")
			}
		
		# Register with FDMS
		client = FDMSClient()
		response = client.register_fiscal_device(device_data)
		
		# Create Fiscal Device document
		fiscal_device = frappe.get_doc({
			"doctype": "Fiscal Device",
			"device_name": device_data.get("device_name", device_data.get("serial_number")),
			"device_type": device_data.get("device_type"),
			"serial_number": device_data.get("serial_number"),
			"taxpayer_tin": device_data.get("taxpayer_tin"),
			"location": device_data.get("location"),
			"fdms_device_id": response.get("device_id"),
			"activation_code": response.get("activation_code"),
			"registration_date": frappe.utils.now(),
			"device_status": "PENDING_ACTIVATION",
		})
		fiscal_device.insert(ignore_permissions=True)
		
		return {
			"status": "success",
			"message": _("Device registered successfully"),
			"device_id": response.get("device_id"),
			"fiscal_device_name": fiscal_device.name,
		}
	
	except FDMSException as e:
		logger.error(f"FDMS registration error: {str(e)}")
		return {"status": "error", "message": str(e)}
	except Exception as e:
		logger.error(f"Unexpected error during registration: {str(e)}")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def activate_fiscal_device(fiscal_device_name: str) -> Dict[str, Any]:
	"""
	Activate a registered fiscal device

	Args:
		fiscal_device_name: Name of the Fiscal Device

	Returns:
		Dictionary with activation result
	"""
	try:
		fiscal_device = frappe.get_doc("Fiscal Device", fiscal_device_name)
		
		if fiscal_device.device_status == "ACTIVE":
			return {
				"status": "info",
				"message": _("Device is already active")
			}
		
		if not fiscal_device.activation_code:
			return {
				"status": "error",
				"message": _("No activation code available")
			}
		
		# Activate with FDMS
		client = FDMSClient()
		response = client.activate_fiscal_device(
			fiscal_device.fdms_device_id,
			fiscal_device.activation_code
		)
		
		# Update device status
		fiscal_device.device_status = "ACTIVE"
		fiscal_device.activation_date = frappe.utils.now()
		fiscal_device.db_update()
		
		return {
			"status": "success",
			"message": _("Device activated successfully"),
		}
	
	except FDMSException as e:
		logger.error(f"FDMS activation error: {str(e)}")
		return {"status": "error", "message": str(e)}
	except Exception as e:
		logger.error(f"Unexpected error during activation: {str(e)}")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_device_status(fiscal_device_name: str) -> Dict[str, Any]:
	"""
	Get the current status of a fiscal device from FDMS

	Args:
		fiscal_device_name: Name of the Fiscal Device

	Returns:
		Dictionary with device status
	"""
	try:
		fiscal_device = frappe.get_doc("Fiscal Device", fiscal_device_name)
		
		# Get status from FDMS
		client = FDMSClient()
		response = client.get_device_status(fiscal_device.fdms_device_id)
		
		# Update device record
		fiscal_device.device_status = response.get("status")
		fiscal_device.last_sync = frappe.utils.now()
		fiscal_device.db_update()
		
		return {
			"status": "success",
			"device_status": response.get("status"),
			"last_sync": frappe.utils.now(),
			"details": response,
		}
	
	except Exception as e:
		logger.error(f"Error fetching device status: {str(e)}")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_device_serial_numbers(fiscal_device_name: str) -> Dict[str, Any]:
	"""
	Get available serial numbers for a device

	Args:
		fiscal_device_name: Name of the Fiscal Device

	Returns:
		Dictionary with serial numbers
	"""
	try:
		fiscal_device = frappe.get_doc("Fiscal Device", fiscal_device_name)
		
		# Get serial numbers from FDMS
		client = FDMSClient()
		response = client.get_device_serial_numbers(fiscal_device.fdms_device_id)
		
		return {
			"status": "success",
			"serial_numbers": response.get("serial_numbers", []),
		}
	
	except Exception as e:
		logger.error(f"Error fetching serial numbers: {str(e)}")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_device_logs(
	fiscal_device_name: str,
	from_date: str = None,
	to_date: str = None
) -> Dict[str, Any]:
	"""
	Get logs from a fiscal device

	Args:
		fiscal_device_name: Name of the Fiscal Device
		from_date: Start date (ISO format)
		to_date: End date (ISO format)

	Returns:
		Dictionary with device logs
	"""
	try:
		fiscal_device = frappe.get_doc("Fiscal Device", fiscal_device_name)
		
		# Get logs from FDMS
		client = FDMSClient()
		response = client.get_device_logs(
			fiscal_device.fdms_device_id,
			from_date,
			to_date
		)
		
		return {
			"status": "success",
			"logs": response.get("logs", []),
		}
	
	except Exception as e:
		logger.error(f"Error fetching device logs: {str(e)}")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def list_fiscal_devices() -> Dict[str, Any]:
	"""
	List all fiscal devices

	Returns:
		Dictionary with list of devices
	"""
	try:
		devices = frappe.get_list(
			"Fiscal Device",
			fields=["name", "serial_number", "device_type", "device_status", "location"],
			order_by="creation desc"
		)
		
		return {
			"status": "success",
			"count": len(devices),
			"devices": devices,
		}
	
	except Exception as e:
		logger.error(f"Error listing devices: {str(e)}")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def sync_device_status(fiscal_device_name: str) -> Dict[str, Any]:
	"""
	Sync device status with FDMS

	Args:
		fiscal_device_name: Name of the Fiscal Device

	Returns:
		Dictionary with sync result
	"""
	try:
		fiscal_device = frappe.get_doc("Fiscal Device", fiscal_device_name)
		
		# Get current status from FDMS
		client = FDMSClient()
		response = client.get_device_status(fiscal_device.fdms_device_id)
		
		# Update device record
		fiscal_device.device_status = response.get("status")
		fiscal_device.last_sync = frappe.utils.now()
		if response.get("error_message"):
			fiscal_device.last_error = response.get("error_message")
		fiscal_device.save(ignore_permissions=True)
		
		return {
			"status": "success",
			"message": _("Device status synced successfully"),
			"device_status": response.get("status"),
		}
	
	except Exception as e:
		logger.error(f"Error syncing device status: {str(e)}")
		return {"status": "error", "message": str(e)}
