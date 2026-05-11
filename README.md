# Verity Fiscal - ERPNext FDMS Integration

An ERPNext application for virtual fiscalisation integrating with the Fiscal Device Management System (FDMS) - Zimbabwe Revenue Authority (ZIMRA) compliant fiscal device gateway.

## Features

- Real-time integration with FDMS for fiscal device management
- Invoice fiscalisation and verification
- Fiscal device registration and management
- Transaction logging and audit trails
- Compliance reporting
- Multi-currency support
- Error handling and retry mechanisms

## Installation

```bash
bench get-app https://github.com/Vickella/verityfiscal.git
bench install-app verityfiscal
```

## Configuration

1. Set FDMS API credentials in System Settings
2. Configure fiscal device settings
3. Enable automatic invoice fiscalisation

## API Documentation

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for detailed API endpoints.

## FDMS Integration

This app integrates with ZIMRA's Fiscal Device Management System (FDMS) API for:

- Device registration and activation
- Invoice transmission and fiscalisation
- Serial number management
- Tax compliance reporting

## License

GNU General Public License v3
