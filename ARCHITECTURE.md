# FDMS Integration Architecture

## Overview

VERITYFiscal provides a complete bridge between ERPNext and the Zimbabwe Revenue Authority (ZIMRA) Fiscal Device Management System (FDMS). The integration follows ZIMRA's Fiscal Device Gateway API v7.2 specifications.

## Architecture Diagram

```
┌─────────────────────┐
│   ERPNext           │
│  (Sales Invoice)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────┐
│  VERITYFiscal App Layer     │
│  ┌───────────────────────┐  │
│  │  Invoice API Module   │  │
│  │  - Fiscalisation      │  │
│  │  - Status Tracking    │  │
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │  Fiscal Device Mgmt   │  │
│  │  - Registration       │  │
│  │  - Activation         │  │
│  │  - Status Monitoring  │  │
│  └───────────────────────┘  │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  FDMS Client Layer          │
│  ┌───────────────────────┐  │
│  │  API Communication    │  │
│  │  - HMAC-SHA256 Auth   │  │
│  │  - Request Signing    │  │
│  │  - Response Handling  │  │
│  └───────────────────────┘  │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  ZIMRA FDMS API             │
│  ┌───────────────────────┐  │
│  │  Fiscal Devices       │  │
│  │  Invoice Processing   │  │
│  │  Compliance Reporting │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

## Key Components

### 1. FDMS Client (`fdms_client.py`)

The core API client for FDMS communication:

- **Authentication**: HMAC-SHA256 signature generation
- **Request/Response Handling**: JSON serialization and error handling
- **Timeout Management**: 30-second default timeout
- **Retry Logic**: Automatic retry on transient failures

**Key Methods**:
- `register_fiscal_device()`: Register new device
- `activate_fiscal_device()`: Activate registered device
- `send_invoice()`: Transmit invoice for fiscalisation
- `get_invoice_status()`: Check invoice fiscal status
- `get_device_status()`: Monitor device health
- `send_batch_invoices()`: Batch transmission

### 2. Invoice API Module (`invoice.py`)

Handles sales invoice fiscalisation:

- **On Submit Hook**: Auto-fiscalise invoices if enabled
- **Status Tracking**: Monitor fiscalisation progress
- **Error Handling**: Graceful failure with logging
- **QR Code Generation**: Fiscal code QR encoding
- **Transaction Logging**: Audit trail creation

**Main Functions**:
- `send_invoice_to_fdms()`: Trigger fiscalisation
- `get_invoice_fiscalisation_status()`: Check status
- `resend_failed_invoice()`: Retry failed invoices

### 3. Fiscal Device Module (`fiscal_device.py`)

Manages fiscal devices:

- **Registration**: New device setup
- **Activation**: Device enablement
- **Health Monitoring**: Status and error tracking
- **Serial Number Management**: Track available serials
- **Log Retrieval**: Access device logs

**Main Functions**:
- `register_fiscal_device()`: Register with FDMS
- `activate_fiscal_device()`: Activate device
- `get_device_status()`: Check current status
- `sync_device_status()`: Force status update

### 4. Utilities (`helpers.py`)

Helper functions and utilities:

- **Data Validation**: TIN format, invoice data structure
- **Encryption**: Sensitive data protection
- **QR Code Generation**: Fiscal code encoding
- **Compliance Reporting**: Data aggregation
- **Device Health**: Health metrics calculation

## Data Flow

### Invoice Fiscalisation Flow

```
1. Submit Sales Invoice
   ├─ Validate invoice data
   ├─ Check fiscal device status
   └─ Prepare invoice payload

2. FDMS API Call
   ├─ Generate HMAC-SHA256 signature
   ├─ Send HTTP POST to /invoices/transmit
   └─ Receive fiscal_code and QR code

3. Update Invoice Document
   ├─ Set fiscal_code
   ├─ Set fiscal_status = "FISCALISED"
   ├─ Generate QR code image
   └─ Save changes

4. Create Transaction Log
   ├─ Record fiscalisation event
   ├─ Store FDMS response
   └─ Maintain audit trail
```

### Device Registration Flow

```
1. Register Device Request
   ├─ Validate device data
   ├─ Check for duplicates
   └─ Call FDMS registration

2. FDMS Returns
   ├─ device_id
   ├─ activation_code
   └─ Registration confirmation

3. Create Fiscal Device Document
   ├─ Store device_id
   ├─ Store activation_code
   ├─ Set status = "PENDING_ACTIVATION"
   └─ Save to database

4. Manual Activation
   ├─ User submits activation_code
   ├─ Call FDMS activation endpoint
   ├─ Set status = "ACTIVE"
   └─ Device ready for use
```

## API Request/Response Examples

### FDMS Invoice Transmission Request

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
      "tax_rate": 15.0
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

### FDMS Invoice Transmission Response

```json
{
  "status": "success",
  "fiscal_code": "ZWL20240115000001",
  "qr_code": "data:image/png;base64,iVBORw0KG...",
  "reference_code": "INV-2024-001",
  "fiscalisation_timestamp": "2024-01-15T10:30:45Z",
  "message": "Invoice successfully fiscalised"
}
```

## Error Handling Strategy

### Categorization

**Transient Errors** (Retryable):
- Network timeouts
- 5xx server errors
- Rate limiting (429)
- Device temporarily offline

**Permanent Errors** (Non-retryable):
- Invalid TIN format
- Duplicate invoice number
- Malformed request
- Invalid device ID
- Expired credentials

### Retry Logic

```python
max_retries = 3
retry_delay = 300  # seconds

for attempt in range(max_retries):
    try:
        response = send_to_fdms()
        return success
    except TransientError as e:
        if attempt < max_retries - 1:
            sleep(retry_delay * (2 ** attempt))  # Exponential backoff
            continue
        else:
            log_failure(e)
```

## Authentication & Security

### HMAC-SHA256 Signature

Each FDMS request is signed to ensure authenticity:

```
1. Create String to Sign:
   METHOD + "\n"
   + ENDPOINT + "\n"
   + TIMESTAMP + "\n"
   + SHA256(request_body)

2. Generate Signature:
   HMAC-SHA256(api_secret, string_to_sign)
   encoded as Base64

3. Add to Headers:
   Authorization: HMAC-SHA256 {api_key}:{signature}
```

### Data Protection

- **In Transit**: HTTPS encryption
- **At Rest**: Encrypted storage for sensitive fields (API keys)
- **In Memory**: Cleared after use
- **Audit Trail**: Complete logging of all operations

## Scalability Considerations

### Rate Limiting

FDMS API limits:
- 1000 requests per hour per API key
- Batch requests count as 1 request
- Implement request queuing for high volume

### Performance Optimization

- Batch invoices when possible (up to 100 per batch)
- Use async processing for non-critical operations
- Cache device status locally (sync every hour)
- Background retry jobs for failed transmissions

### Database Optimization

- Index on `fiscal_code` for quick lookups
- Index on `posting_date` for compliance reporting
- Archive old transaction logs for performance

## Compliance & Audit

### Transaction Logging

Every FDMS interaction is logged:
- Request timestamp
- Response status
- Fiscal code (if success)
- Error details (if failure)
- User/system that triggered action

### Compliance Reporting

Automatic daily reports include:
- Total invoices fiscalised
- Total amount and taxes collected
- Failed transactions
- Device status summary

### Retention Policy

- Transaction logs: 7 years (ZIMRA requirement)
- Device logs: 5 years
- Compliance reports: Indefinite

## Testing

### Development Environment

Use sandbox environment for testing:
- Test device registration
- Test invoice fiscalisation
- Verify error handling
- No actual fiscal data transmitted

### Test Scenarios

1. **Happy Path**: Successful fiscalisation
2. **Retry Scenario**: Transient failure then success
3. **Permanent Failure**: Invalid data handling
4. **Device Offline**: Status monitoring
5. **Rate Limiting**: Backoff strategy

## Future Enhancements

1. **Device Clustering**: Multiple devices per location
2. **Invoice Templates**: Customizable formatting
3. **Multi-Currency**: Enhanced currency support
4. **Payment Integration**: Direct payment status sync
5. **Advanced Analytics**: Dashboard and reporting
6. **Mobile Support**: Mobile invoice submission

## References

- ZIMRA FDMS API Documentation v7.2
- ERPNext Framework Documentation
- Frappe Server API Reference
- HMAC-SHA256 Specification (RFC 4868)
