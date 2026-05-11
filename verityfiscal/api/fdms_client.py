import frappe
import requests
import json
import hashlib
import hmac
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List
from requests.auth import HTTPBasicAuth
import logging

logger = logging.getLogger(__name__)


class FDMSClient:
	"""
	ZIMRA Fiscal Device Management System (FDMS) API Client
	Handles all communication with FDMS for fiscal device management and invoice fiscalisation
	"""

	def __init__(self, api_key: str = None, api_secret: str = None, environment: str = "production"):
		"""
		Initialize FDMS Client

		Args:
			api_key: FDMS API key
			api_secret: FDMS API secret
			environment: "production" or "sandbox"
		"""
		self.settings = frappe.get_doc("FDMS Settings") if frappe.db.exists("FDMS Settings") else None
		
		self.api_key = api_key or (self.settings.api_key if self.settings else None)
		self.api_secret = api_secret or (self.settings.api_secret if self.settings else None)
		self.environment = environment or (self.settings.environment if self.settings else "production")
		
		self.base_url = self._get_base_url()
		self.timeout = 30
		self.session = requests.Session()

	def _get_base_url(self) -> str:
		"""Get the base URL based on environment"""
		if self.environment == "sandbox":
			return "https://sandbox-fdms.zimra.co.zw/api/v2"
		else:
			return "https://fdms.zimra.co.zw/api/v2"

	def _generate_signature(self, method: str, endpoint: str, payload: Dict = None, timestamp: str = None) -> str:
		"""
		Generate HMAC-SHA256 signature for FDMS API requests

		Args:
			method: HTTP method (GET, POST, PUT, DELETE)
			endpoint: API endpoint
			payload: Request body
			timestamp: Request timestamp

		Returns:
			Signature string
		"""
		timestamp = timestamp or datetime.utcnow().isoformat() + "Z"
		
		# Create the string to sign
		if payload:
			body_hash = hashlib.sha256(json.dumps(payload).encode()).hexdigest()
		else:
			body_hash = hashlib.sha256(b"").hexdigest()
		
		string_to_sign = f"{method}\n{endpoint}\n{timestamp}\n{body_hash}"
		
		# Generate HMAC-SHA256 signature
		signature = hmac.new(
			self.api_secret.encode(),
			string_to_sign.encode(),
			hashlib.sha256
		).digest()
		
		return base64.b64encode(signature).decode()

	def _get_headers(self, method: str, endpoint: str, payload: Dict = None) -> Dict[str, str]:
		"""Generate request headers with authentication"""
		timestamp = datetime.utcnow().isoformat() + "Z"
		signature = self._generate_signature(method, endpoint, payload, timestamp)
		
		return {
			"Content-Type": "application/json",
			"Authorization": f"HMAC-SHA256 {self.api_key}:{signature}",
			"X-Request-Timestamp": timestamp,
			"User-Agent": "ERPNext-VERITYFiscal/1.0",
		}

	def _make_request(
		self, 
		method: str, 
		endpoint: str, 
		data: Dict = None, 
		params: Dict = None
	) -> Dict[str, Any]:
		"""
		Make HTTP request to FDMS API

		Args:
			method: HTTP method
			endpoint: API endpoint
			data: Request body data
			params: Query parameters

		Returns:
			Response dictionary
		"""
		url = f"{self.base_url}{endpoint}"
		headers = self._get_headers(method, endpoint, data)
		
		try:
			response = self.session.request(
				method=method,
				url=url,
				json=data,
				params=params,
				headers=headers,
				timeout=self.timeout,
			)
			
			response.raise_for_status()
			return response.json()
		
		except requests.exceptions.RequestException as e:
			logger.error(f"FDMS API Error: {str(e)}")
			raise FDMSException(f"FDMS API request failed: {str(e)}")

	def register_fiscal_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Register a new fiscal device with FDMS

		Args:
			device_data: Device registration data
				- device_type: Device type code
				- serial_number: Device serial number
				- taxpayer_tin: Tax payer identification number
				- location: Device location

		Returns:
			Registration response with device_id and activation_code
		"""
		endpoint = "/fiscal-devices/register"
		
		payload = {
			"device_type": device_data.get("device_type"),
			"serial_number": device_data.get("serial_number"),
			"taxpayer_tin": device_data.get("taxpayer_tin"),
			"location": device_data.get("location"),
			"activation_key": device_data.get("activation_key"),
		}
		
		response = self._make_request("POST", endpoint, payload)
		return response

	def activate_fiscal_device(self, device_id: str, activation_code: str) -> Dict[str, Any]:
		"""
		Activate a fiscal device

		Args:
			device_id: Device ID from registration
			activation_code: Activation code provided during registration

		Returns:
			Activation response
		"""
		endpoint = f"/fiscal-devices/{device_id}/activate"
		
		payload = {
			"activation_code": activation_code,
		}
		
		response = self._make_request("POST", endpoint, payload)
		return response

	def get_device_status(self, device_id: str) -> Dict[str, Any]:
		"""
		Get the current status of a fiscal device

		Args:
			device_id: Device ID

		Returns:
			Device status information
		"""
		endpoint = f"/fiscal-devices/{device_id}/status"
		response = self._make_request("GET", endpoint)
		return response

	def send_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Send an invoice to FDMS for fiscalisation

		Args:
			invoice_data: Invoice data dictionary with:
				- invoice_number: Unique invoice number
				- invoice_date: Invoice date (ISO format)
				- customer_tin: Customer TIN (if applicable)
				- items: List of invoice items
				- total_amount: Total invoice amount
				- tax_amount: Total tax amount
				- currency: Currency code

		Returns:
			Fiscalisation response with fiscal code and QR code
		"""
		endpoint = "/invoices/transmit"
		
		payload = {
			"invoice_number": invoice_data.get("invoice_number"),
			"invoice_date": invoice_data.get("invoice_date"),
			"invoice_type": invoice_data.get("invoice_type", "REGULAR"),
			"customer_tin": invoice_data.get("customer_tin"),
			"customer_name": invoice_data.get("customer_name"),
			"items": invoice_data.get("items", []),
			"subtotal": invoice_data.get("subtotal", 0),
			"tax_amount": invoice_data.get("tax_amount", 0),
			"total_amount": invoice_data.get("total_amount", 0),
			"currency": invoice_data.get("currency", "ZWL"),
			"device_id": invoice_data.get("device_id"),
			"reference_code": invoice_data.get("reference_code"),
		}
		
		response = self._make_request("POST", endpoint, payload)
		return response

	def get_invoice_status(self, fiscal_code: str) -> Dict[str, Any]:
		"""
		Get the fiscalisation status of an invoice

		Args:
			fiscal_code: Fiscal code from fiscalisation response

		Returns:
			Invoice status information
		"""
		endpoint = f"/invoices/{fiscal_code}/status"
		response = self._make_request("GET", endpoint)
		return response

	def get_device_serial_numbers(self, device_id: str) -> Dict[str, Any]:
		"""
		Get available serial numbers for a device

		Args:
			device_id: Device ID

		Returns:
			List of available serial numbers
		"""
		endpoint = f"/fiscal-devices/{device_id}/serial-numbers"
		response = self._make_request("GET", endpoint)
		return response

	def verify_invoice(self, invoice_number: str, fiscal_code: str) -> Dict[str, Any]:
		"""
		Verify an invoice with FDMS

		Args:
			invoice_number: Invoice number
			fiscal_code: Fiscal code from FDMS

		Returns:
			Verification result
		"""
		endpoint = f"/invoices/verify"
		
		payload = {
			"invoice_number": invoice_number,
			"fiscal_code": fiscal_code,
		}
		
		response = self._make_request("POST", endpoint, payload)
		return response

	def get_device_logs(self, device_id: str, from_date: str = None, to_date: str = None) -> Dict[str, Any]:
		"""
		Get logs from a fiscal device

		Args:
			device_id: Device ID
			from_date: Start date (ISO format)
			to_date: End date (ISO format)

		Returns:
			Device logs
		"""
		endpoint = f"/fiscal-devices/{device_id}/logs"
		
		params = {}
		if from_date:
			params["from_date"] = from_date
		if to_date:
			params["to_date"] = to_date
		
		response = self._make_request("GET", endpoint, params=params)
		return response

	def send_batch_invoices(self, invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
		"""
		Send multiple invoices in a batch

		Args:
			invoices: List of invoice data dictionaries

		Returns:
			Batch response with individual invoice results
		"""
		endpoint = "/invoices/batch-transmit"
		
		payload = {
			"invoices": invoices,
		}
		
		response = self._make_request("POST", endpoint, payload)
		return response

	def get_compliance_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
		"""
		Get compliance data for a date range

		Args:
			start_date: Start date (ISO format)
			end_date: End date (ISO format)

		Returns:
			Compliance data
		"""
		endpoint = "/compliance/data"
		
		params = {
			"start_date": start_date,
			"end_date": end_date,
		}
		
		response = self._make_request("GET", endpoint, params=params)
		return response


class FDMSException(Exception):
	"""Custom exception for FDMS API errors"""
	pass
