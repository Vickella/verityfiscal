# VERITYFiscal Installation Guide

## Prerequisites

- ERPNext v15 or higher
- Frappe Framework v15 or higher
- Python 3.8+
- Bench CLI installed

## Installation Steps

### 1. Clone the Repository

```bash
cd ~/frappe-bench
bench get-app https://github.com/verityfiscal/verityfiscal.git
```

### 2. Install the App

```bash
bench install-app verityfiscal
```

### 3. Configure FDMS Settings

1. Go to **Setup > System Settings** or navigate to **Verity Fiscal > FDMS Settings**
2. Enable FDMS Integration
3. Enter your FDMS API credentials:
   - API Key
   - API Secret
   - Select environment (Sandbox or Production)

### 4. Create Fiscal Devices

1. Go to **Verity Fiscal > Fiscal Device**
2. Click **New** to create a new device
3. Fill in device details:
   - Device Name
   - Device Type (PRINTER, CASH_REGISTER, POS_TERMINAL, WEB_SERVICE)
   - Serial Number
   - Taxpayer TIN
   - Location
4. Click **Register** button to register with FDMS

### 5. Activate Fiscal Devices

Once registered, you'll receive an activation code:
1. Open the registered device
2. Provide the activation code
3. Click **Activate** button

### 6. Configure Sales Invoice

The app automatically adds the following fields to Sales Invoice:
- Fiscal Device (select the device to use)
- Fiscal Status (auto-populated)
- Fiscal Code (auto-populated after fiscalisation)
- QR Code (auto-populated)

## Configuration Options

### Auto-Fiscalisation

To automatically fiscalise invoices when submitted:
1. Go to **Verity Fiscal > FDMS Settings**
2. Check **Auto-Fiscalise on Invoice Submit**
3. Save

### Retry Configuration

For automatic retry of failed transmissions:
1. Go to **Verity Fiscal > FDMS Settings**
2. Check **Retry Failed Transmissions**
3. Set **Retry Attempts** (default: 3)
4. Set **Retry Interval** in seconds (default: 300)

### Compliance Reporting

To generate automatic compliance reports:
1. Go to **Verity Fiscal > FDMS Settings**
2. Check **Generate Compliance Reports**
3. Select **Compliance Report Frequency**

## Usage

### Fiscalise an Invoice

#### Manual Fiscalisation

1. Create and submit a Sales Invoice
2. Select a Fiscal Device in the **Fiscal Device** field
3. Click **Fiscalise** button (appears after submission)

#### Automatic Fiscalisation

If auto-fiscalisation is enabled, invoices are automatically fiscalised on submission.

### Check Invoice Status

1. Open the Sales Invoice
2. The **Fiscal Status** field shows the current status:
   - PENDING: Waiting to be fiscalised
   - FISCALISED: Successfully fiscalised
   - FAILED: Fiscalisation failed
   - CANCELLED: Invoice has been cancelled

### View Transaction Logs

All FDMS transactions are logged:
1. Go to **Verity Fiscal > FDMS Transaction Log**
2. View detailed transaction history
3. See request/response data for debugging

### Monitor Device Status

1. Go to **Verity Fiscal > Fiscal Device**
2. Click on a device to view:
   - Current status
   - Last sync time
   - Error messages (if any)
   - Device logs

## API Usage

### Using ERPNext Methods

All functionality is exposed via ERPNext API methods. Examples:

```bash
# Fiscalise an invoice
curl -X POST http://localhost:8000/api/method/verityfiscal.api.invoice.send_invoice_to_fdms \
  -H "X-Frappe-CSRF-Token: <token>" \
  -d "invoice_name=INV-2024-001"

# Get invoice status
curl -X POST http://localhost:8000/api/method/verityfiscal.api.invoice.get_invoice_fiscalisation_status \
  -H "X-Frappe-CSRF-Token: <token>" \
  -d "invoice_name=INV-2024-001"

# Register fiscal device
curl -X POST http://localhost:8000/api/method/verityfiscal.api.fiscal_device.register_fiscal_device \
  -H "X-Frappe-CSRF-Token: <token>" \
  -d "device_data={...}"
```

### Direct Python Usage

```python
from verityfiscal.api.fdms_client import FDMSClient

client = FDMSClient()
response = client.send_invoice({
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-01-15T10:00:00Z",
    "customer_name": "John Doe",
    "items": [...],
    "total_amount": 230.00,
})
```

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete API reference.

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to FDMS API

**Solutions**:
1. Verify API credentials in **FDMS Settings**
2. Check network connectivity
3. Ensure you're using the correct environment (Sandbox vs Production)
4. Review [FDMS Transaction Log](https://erp.example.com/app/fdms-transaction-log) for error details

### Invoice Fiscalisation Failed

**Problem**: Invoice fiscalisation returns error

**Common Causes**:
1. Fiscal device not active - Ensure device status is "ACTIVE"
2. Invalid invoice data - Check that all required fields are populated
3. Duplicate invoice number - Each invoice must have unique number
4. Missing tax ID - If customer has TIN, it must be valid format

**Resolution**:
1. Review the error message in the invoice
2. Check [FDMS Transaction Log](https://erp.example.com/app/fdms-transaction-log) for details
3. Correct the issue and retry fiscalisation using **Resend** button

### Device Not Syncing

**Problem**: Device status not updating

**Solutions**:
1. Ensure auto-sync is enabled in **FDMS Settings**
2. Manually sync by clicking **Sync** button on device
3. Check network connectivity
4. Verify device is still active on FDMS side

## Database Reset (Development Only)

To reset the app for testing:

```bash
bench --site <site-name> execute verityfiscal.scripts.reset_app
```

## Support & Documentation

- **API Documentation**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **GitHub Issues**: Report bugs and feature requests
- **Email Support**: support@verityfiscal.com

## Security Considerations

1. **API Credentials**: Store securely in environment variables, never in code
2. **Data Encryption**: Sensitive data is encrypted at rest and in transit
3. **Audit Logging**: All transactions are logged for compliance
4. **Rate Limiting**: Respect FDMS rate limits (1000 requests/hour)

## License

GNU General Public License v3 - See LICENSE file for details
