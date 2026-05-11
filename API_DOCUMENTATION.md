# VERITYFiscal API Documentation

## Overview

VERITYFiscal is an ERPNext application that integrates with the Zimbabwe Revenue Authority (ZIMRA) Fiscal Device Management System (FDMS) for virtual fiscalisation of invoices. This API documentation covers all available endpoints for integrating ERPNext with the FDMS.

## Base URL

- **Production**: `https://fdms.zimra.co.zw/api/v2`
- **Sandbox**: `https://sandbox-fdms.zimra.co.zw/api/v2`

## Authentication

All API requests must include the following headers:

```
Content-Type: application/json
Authorization: HMAC-SHA256 {api_key}:{signature}
X-Request-Timestamp: {timestamp}
User-Agent: ERPNext-VERITYFiscal/1.0
```

### Signature Generation

The signature is generated using HMAC-SHA256:

```
String to Sign = METHOD + "\n" + ENDPOINT + "\n" + TIMESTAMP + "\n" + BODY_HASH

BODY_HASH = SHA256(json_encoded_body)
SIGNATURE = Base64(HMAC-SHA256(API_SECRET, String to Sign))
```

## API Endpoints

### 1. Fiscal Device Management

#### Register Fiscal Device

Register a new fiscal device with FDMS.

**Endpoint**: `POST /fiscal-devices/register`

**Request**:
```json
{
  "device_type": "PRINTER",
  "serial_number": "FD-2024-001",
  "taxpayer_tin": "1234567890",
  "location": "Main Store",
  "activation_key": "ACTIVATION_KEY_HERE"
}
```

**Response** (Success):
```json
{
  "status": "success",
  "device_id": "DEV-20240115-001",
  "activation_code": "ACTIVATION_CODE_HERE",
  "message": "Device registered successfully"
}
```

**ERPNext Endpoint**:
```
POST /api/method/verityfiscal.api.fiscal_device.register_fiscal_device
```

---

#### Activate Fiscal Device

Activate a registered fiscal device.

**Endpoint**: `POST /fiscal-devices/{device_id}/activate`

**Request**:
```json
{
  "activation_code": "ACTIVATION_CODE_HERE"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Device activated successfully"
}
```

**ERPNext Endpoint**:
```
POST /api/method/verityfiscal.api.fiscal_device.activate_fiscal_device
Parameters:
- fiscal_device_name: Name of the Fiscal Device
```

---

#### Get Device Status

Get the current status of a fiscal device.

**Endpoint**: `GET /fiscal-devices/{device_id}/status`

**Response**:
```json
{
  "device_id": "DEV-20240115-001",
  "status": "ACTIVE",
  "last_heartbeat": "2024-01-15T10:30:00Z",
  "serial_number": "FD-2024-001",
  "certificates_valid_until": "2025-01-15"
}
```

**ERPNext Endpoint**:
```
POST /api/method/verityfiscal.api.fiscal_device.get_device_status
Parameters:
- fiscal_device_name: Name of the Fiscal Device
```

---

#### Get Device Serial Numbers

Retrieve available serial numbers for a device.

**Endpoint**: `GET /fiscal-devices/{device_id}/serial-numbers`

**Response**:
```json
{
  "status": "success",
  "serial_numbers": [
    {
      "serial": "00001",
      "used": false,
      "issued_date": "2024-01-15"
    },
    {
      "serial": "00002",
      "used": false,
      "issued_date": "2024-01-15"
    }
  ]
}
```

**ERPNext Endpoint**:
```
POST /api/method/verityfiscal.api.fiscal_device.get_device_serial_numbers
Parameters:
- fiscal_device_name: Name of the Fiscal Device
```

---

#### Get Device Logs

Retrieve logs from a fiscal device.

**Endpoint**: `GET /fiscal-devices/{device_id}/logs?from_date={from}&to_date={to}`

**Response**:
```json
{
  "status": "success",
  "logs": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "event": "INVOICE_TRANSMITTED",
      "invoice_number": "INV-2024-001",
      "status": "SUCCESS"
    }
  ]
}
```

**ERPNext Endpoint**:
```
POST /api/method/verityfiscal.api.fiscal_device.get_device_logs
Parameters:
- fiscal_device_name: Name of the Fiscal Device
- from_date: Start date (ISO format)
- to_date: End date (ISO format)
```

---

#### List Fiscal Devices

Get all fiscal devices.

**ERPNext Endpoint**:
```
POST /api/method/verityfiscal.api.fiscal_device.list_fiscal_devices
```

**Response**:
```json
{
  "status": "success",
  "count": 2,
  "devices": [
    {
      "name": "FD-PRINTER-001",
      "serial_number": "FD-2024-001",
      "device_type": "PRINTER",
      "device_status": "ACTIVE",
      "location": "Main Store"
    }
  ]
}
```

---

### 2. Invoice Fiscalisation

#### Send Invoice to FDMS

Transmit an invoice to FDMS for fiscalisation.

**Endpoint**: `POST /invoices/transmit`

**Request**:
```json
{
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-01-15T10:00:00Z",
  "invoice_type": "REGULAR",
  "customer_tin": "1234567890",
  "customer_name": "John Doe",
  "items": [
    {
      "description": "Product A",
      "quantity": 2,
      "unit_price": 100.00,
      "amount": 200.00,
      "tax_rate": 15
    }
  ],
  "subtotal": 200.00,
  "tax_amount": 30.00,
  "total_amount": 230.00,
  "currency": "ZWL",
  "device_id": "DEV-20240115-001",
  "reference_code": "INV-2024-001"
}
```

**Response** (Success):
```json
{
  "status": "success",
  "fiscal_code": "ZWL20240115000001",
  "qr_code": "https://fdms.zimra.co.zw/qr/ZWL20240115000001",
  "reference_code": "INV-2024-001",
  "message": "Invoice fiscalised successfully"
}
```

**ERPNext Endpoint**:
```
POST /api/method/verityfiscal.api.invoice.send_invoice_to_fdms
Parameters:
- invoice_name: Name of the Sales Invoice
```

---

#### Get Invoice Fiscalisation Status

Check the status of a fiscalised invoice.

**Endpoint**: `GET /invoices/{fiscal_code}/status`

**Response**:
```json
{
  "status": "FISCALISED",
  "fiscal_code": "ZWL20240115000001",
  "invoice_number": "INV-2024-001",
  "fiscalisation_timestamp": "2024-01-15T10:30:00Z",
  "message": "Invoice successfully fiscalised"
}
```

**ERPNext Endpoint**:
```
POST /api/method/verityfiscal.api.invoice.get_invoice_fiscalisation_status
Parameters:
- invoice_name: Name of the Sales Invoice
```

---

#### Verify Invoice

Verify an invoice with FDMS.

**Endpoint**: `POST /invoices/verify`

**Request**:
```json
{
  "invoice_number": "INV-2024-001",
  "fiscal_code": "ZWL20240115000001"
}
```

**Response**:
```json
{
  "status": "success",
  "verified": true,
  "message": "Invoice verified successfully"
}
```

---

#### Resend Failed Invoice

Retry sending a failed invoice.

**ERPNext Endpoint**:
```
POST /api/method/verityfiscal.api.invoice.resend_failed_invoice
Parameters:
- invoice_name: Name of the Sales Invoice
```

---

#### Send Batch Invoices

Send multiple invoices in a batch request.

**Endpoint**: `POST /invoices/batch-transmit`

**Request**:
```json
{
  "invoices": [
    {
      "invoice_number": "INV-2024-001",
      "invoice_date": "2024-01-15T10:00:00Z",
      ...
    },
    {
      "invoice_number": "INV-2024-002",
      "invoice_date": "2024-01-15T10:05:00Z",
      ...
    }
  ]
}
```

**Response**:
```json
{
  "status": "success",
  "batch_id": "BATCH-20240115-001",
  "results": [
    {
      "invoice_number": "INV-2024-001",
      "status": "success",
      "fiscal_code": "ZWL20240115000001"
    },
    {
      "invoice_number": "INV-2024-002",
      "status": "success",
      "fiscal_code": "ZWL20240115000002"
    }
  ]
}
```

---

### 3. Compliance & Reporting

#### Get Compliance Data

Retrieve compliance data for a date range.

**Endpoint**: `GET /compliance/data?start_date={start}&end_date={end}`

**Response**:
```json
{
  "status": "success",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "invoices_count": 150,
  "total_amount": 45000.00,
  "tax_collected": 6750.00,
  "summary": {
    "daily_breakdown": [...]
  }
}
```

---

## Error Handling

All API responses follow this error format:

```json
{
  "status": "error",
  "error_code": "INVALID_DEVICE_ID",
  "message": "The specified device ID does not exist",
  "details": {
    "device_id": "DEV-INVALID"
  }
}
```

### Common Error Codes

| Code | Meaning |
|------|---------|
| `INVALID_REQUEST` | Missing or invalid request parameters |
| `AUTHENTICATION_FAILED` | Invalid API credentials |
| `INVALID_DEVICE_ID` | Device ID not found or inactive |
| `INVOICE_ALREADY_FISCALISED` | Invoice already has a fiscal code |
| `INVALID_INVOICE_DATA` | Invoice data validation failed |
| `DEVICE_NOT_ACTIVE` | Device is not in active status |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `SERVER_ERROR` | Internal server error |

---

## Webhook Events

FDMS sends webhook notifications for the following events:

### Device Status Changed

```json
{
  "event": "device.status_changed",
  "device_id": "DEV-20240115-001",
  "previous_status": "ACTIVE",
  "current_status": "OFFLINE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Invoice Status Changed

```json
{
  "event": "invoice.status_changed",
  "fiscal_code": "ZWL20240115000001",
  "invoice_number": "INV-2024-001",
  "status": "REJECTED",
  "reason": "Duplicate invoice number",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Rate Limiting

- 1000 requests per hour per API key
- Batch requests count as 1 request regardless of invoice count
- Responses include `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers

---

## ERPNext Integration Features

### 1. Sales Invoice Enhancement

When a Sales Invoice is submitted with FDMS enabled:
- Automatic fiscalisation (if enabled)
- Fiscal code and QR code generation
- Status tracking in the invoice document

### 2. Fiscal Device Management

Full interface for:
- Registering new fiscal devices
- Activating devices
- Monitoring device status and health
- Viewing device logs and transaction history

### 3. Transaction Logging

All FDMS transactions are logged for:
- Audit trail
- Compliance reporting
- Troubleshooting
- Performance analysis

### 4. Scheduled Tasks

Automatic background jobs:
- Hourly: Sync device status
- Daily: Reconcile failed transactions and generate compliance reports

---

## Configuration

### FDMS Settings

Access via **Verity Fiscal > FDMS Settings**

**Required Fields**:
- API Key
- API Secret
- Environment (sandbox/production)

**Optional Settings**:
- Auto-fiscalise on invoice submit
- Auto sync device status
- Retry failed transmissions
- Generate compliance reports

---

## Code Examples

### Python Example

```python
from verityfiscal.api.fdms_client import FDMSClient

# Initialize client
client = FDMSClient(
    api_key="your_api_key",
    api_secret="your_api_secret",
    environment="production"
)

# Register device
response = client.register_fiscal_device({
    "device_type": "PRINTER",
    "serial_number": "FD-2024-001",
    "taxpayer_tin": "1234567890",
    "location": "Main Store",
})

# Send invoice
response = client.send_invoice({
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-01-15T10:00:00Z",
    "customer_name": "John Doe",
    "items": [...],
    "total_amount": 230.00,
    "device_id": response["device_id"]
})
```

### JavaScript/TypeScript Example

```javascript
// Using ERPNext's frappe.call

frappe.call({
    method: "verityfiscal.api.invoice.send_invoice_to_fdms",
    args: {
        invoice_name: "INV-2024-001"
    },
    callback: function(r) {
        if (r.message.status === "success") {
            frappe.msgprint("Invoice fiscalised successfully!");
            console.log("Fiscal Code: " + r.message.fiscal_code);
        }
    }
});
```

---

## Support

For issues or questions:
1. Check the [FDMS Settings](https://erp.example.com/app/fdms-settings)
2. Review [FDMS Transaction Logs](https://erp.example.com/app/fdms-transaction-log)
3. Contact support at support@verityfiscal.com

---

## Changelog

### Version 1.0.0 (2024-01-15)
- Initial release
- Fiscal device registration and activation
- Invoice fiscalisation
- Device status monitoring
- Compliance reporting
- Transaction logging
