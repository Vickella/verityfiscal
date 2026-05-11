# VERITYFiscal - Quick Start Guide

## What is VERITYFiscal?

VERITYFiscal is an **ERPNext application** that integrates your financial system with Zimbabwe's **Fiscal Device Management System (FDMS)** from ZIMRA (Zimbabwe Revenue Authority). It enables virtual fiscalisation of invoices for complete tax compliance.

## 5-Minute Setup

### Step 1: Install the App

```bash
cd ~/frappe-bench
bench get-app https://github.com/Vickella/verityfiscal.git
bench install-app verityfiscal --site your_site_name
```

### Step 2: Configure FDMS Credentials

1. Go to **Verity Fiscal > FDMS Settings**
2. Enable FDMS Integration
3. Enter your FDMS API credentials:
   - API Key
   - API Secret
   - Select environment (Sandbox for testing, Production for live)
4. Save

### Step 3: Register a Fiscal Device

1. Go to **Verity Fiscal > Fiscal Device**
2. Click **+ New**
3. Fill in:
   - Device Name: e.g., "Main POS Terminal"
   - Device Type: Select from dropdown
   - Serial Number: Device serial
   - Taxpayer TIN: Your Tax ID
   - Location: e.g., "Main Store"
4. Click **Register with FDMS**
5. You'll receive an activation code
6. Click **Activate Device**

### Step 4: Create a Sales Invoice

1. Go to **Accounting > Sales Invoice**
2. Create a new invoice normally
3. In the "Fiscal Details" section, select your registered Fiscal Device
4. Submit the invoice

### Step 5: Fiscalise the Invoice

**If you have auto-fiscalisation enabled:**
- Invoice is automatically fiscalised on submission ✓

**If manual fiscalisation:**
1. Click **Fiscalise** button
2. Fiscal code and QR code are generated automatically
3. QR code can be printed or displayed on receipts

## Key Features

### ✅ Automatic Invoice Fiscalisation
- Configure to auto-fiscalise on invoice submission
- Never miss a fiscal requirement

### ✅ Real-time Device Monitoring
- View device status, errors, and health metrics
- Get alerts when devices go offline

### ✅ Complete Audit Trail
- Every transaction is logged
- 7-year compliance data retention
- Full transaction history for audits

### ✅ Automatic Compliance Reporting
- Daily, weekly, or monthly reports
- Tax collection summaries
- Transaction success/failure analysis

### ✅ Intelligent Retry System
- Failed transmissions automatically retry
- Configurable retry attempts and intervals
- Exponential backoff strategy

### ✅ Multi-Device Support
- Support multiple fiscal devices per location
- Automatic device failover
- Device load balancing

## Common Operations

### Fiscalise an Invoice
```python
# Via UI: Click "Fiscalise" button on submitted invoice

# Via API:
curl -X POST http://localhost:8000/api/method/verityfiscal.api.invoice.send_invoice_to_fdms \
  -d "invoice_name=INV-2024-001"
```

### Check Invoice Status
```python
# Via UI: Open invoice, check "Fiscal Status" field

# Via API:
curl -X POST http://localhost:8000/api/method/verityfiscal.api.invoice.get_invoice_fiscalisation_status \
  -d "invoice_name=INV-2024-001"
```

### Monitor Fiscal Device
```python
# Via UI: Open Fiscal Device, click "Get Status"

# Via API:
curl -X POST http://localhost:8000/api/method/verityfiscal.api.fiscal_device.get_device_status \
  -d "fiscal_device_name=FD-PRINTER-001"
```

### View Transaction Logs
**Menu:** Verity Fiscal > FDMS Transaction Log

See all fiscalisation attempts, successes, failures, and retries.

## Configuration Options

### Auto-Fiscalisation
**Verity Fiscal > FDMS Settings**

```
☑ Auto-Fiscalise on Invoice Submit
```

When enabled, invoices are automatically fiscalised when submitted.

### Automatic Retry
**Verity Fiscal > FDMS Settings**

```
☑ Retry Failed Transmissions
Retry Attempts: 3
Retry Interval: 300 (seconds)
```

### Compliance Reporting
**Verity Fiscal > FDMS Settings**

```
☑ Generate Compliance Reports
Frequency: Daily/Weekly/Monthly
```

### Device Auto-Sync
**Verity Fiscal > FDMS Settings**

```
☑ Auto Sync Device Status
```

Devices automatically sync status every hour.

## Troubleshooting

### Invoice Won't Fiscalise

**Problem**: "Device not found" or "Device not active"

**Solution**:
1. Check that Fiscal Device exists and is ACTIVE
2. Open device and click "Get Status" to verify
3. If offline, activate device again

**Problem**: "Invalid invoice data"

**Solution**:
1. Check all invoice fields are filled
2. Ensure customer name is entered
3. Verify items have quantities and prices
4. Check that amounts are positive

**Problem**: "Duplicate invoice number"

**Solution**:
1. Invoice number must be unique within same device
2. Check existing transactions
3. Use different invoice numbering system if needed

### Device Not Syncing

**Problem**: Device status stuck as "PENDING_ACTIVATION"

**Solution**:
1. Go to Fiscal Device
2. Click "Sync Status" button
3. If still pending, check activation code and re-activate
4. Review FDMS Transaction Log for error details

### High Transaction Failure Rate

**Problem**: Many failed transmissions

**Solution**:
1. Check network connectivity
2. Verify FDMS API credentials
3. Check FDMS system status at https://status.zimra.co.zw
4. Review device logs: **Fiscal Device > Get Logs**

## Module Structure

```
verityfiscal/
├── api/
│   ├── fdms_client.py       # FDMS API client
│   ├── invoice.py           # Invoice fiscalisation
│   └── fiscal_device.py     # Device management
├── doctype/
│   ├── fiscal_device.json
│   ├── fdms_settings.json
│   ├── fdms_transaction_log.json
│   └── compliance_report.json
├── utils/
│   └── helpers.py           # Utilities and helpers
├── tasks.py                 # Scheduled tasks
├── hooks.py                 # App hooks
└── __init__.py
```

## API Endpoints

All endpoints are exposed via ERPNext API:

**Fiscal Device Management:**
- `verityfiscal.api.fiscal_device.register_fiscal_device`
- `verityfiscal.api.fiscal_device.activate_fiscal_device`
- `verityfiscal.api.fiscal_device.get_device_status`
- `verityfiscal.api.fiscal_device.list_fiscal_devices`

**Invoice Fiscalisation:**
- `verityfiscal.api.invoice.send_invoice_to_fdms`
- `verityfiscal.api.invoice.get_invoice_fiscalisation_status`
- `verityfiscal.api.invoice.resend_failed_invoice`

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete reference.

## Best Practices

### 1. Use Unique Invoice Numbers
- Each invoice must have unique number per device
- Use sequential numbering for easy tracking
- Avoid duplicates across time periods

### 2. Verify Device Health Regularly
- Check device status weekly
- Review error logs for patterns
- Monitor failed transmission rate

### 3. Test in Sandbox First
- Always test new configurations in sandbox
- Verify FDMS settings before production
- Test all critical workflows

### 4. Maintain Backups
- Regular database backups
- Keep FDMS credentials secure
- Document your configuration

### 5. Monitor Compliance
- Review daily compliance reports
- Track tax collection metrics
- Maintain audit trails

## Support Resources

- **Detailed Documentation**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Installation Guide**: [INSTALLATION.md](./INSTALLATION.md)
- **Architecture**: [ARCHITECTURE.md](./ARCHITECTURE.md)
- **ZIMRA FDMS**: https://www.zimra.co.zw/

## Next Steps

1. ✅ Install the application
2. ✅ Configure FDMS settings
3. ✅ Register fiscal devices
4. ✅ Create test invoice
5. ✅ Fiscalise and verify
6. ✅ Set up compliance reports
7. ✅ Enable auto-fiscalisation (optional)
8. ✅ Go live in production

## License

GNU General Public License v3

---

**Ready to get started?** Head to [INSTALLATION.md](./INSTALLATION.md) for detailed setup instructions.

**Have questions?** Check [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for comprehensive API reference.

**Want to understand the architecture?** See [ARCHITECTURE.md](./ARCHITECTURE.md) for technical deep-dive.
