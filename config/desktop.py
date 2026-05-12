from frappe import _


def get_data():
    return [
        {
            "module_name": "Verity Fiscal",
            "color": "#4472c4",
            "icon": "octicon octicon-file-code",
            "type": "module",
            "label": _("Verity Fiscal"),
            "description": _("Fiscalisation and FDMS integration for ERPNext."),
            "items": [
                {
                    "type": "doctype",
                    "name": "FDMS Settings",
                    "label": _("FDMS Settings"),
                    "description": _("Configure FDMS API credentials and fiscalisation settings."),
                },
                {
                    "type": "doctype",
                    "name": "Fiscal Device",
                    "label": _("Fiscal Device"),
                    "description": _("Manage fiscal devices registered with FDMS."),
                },
                {
                    "type": "doctype",
                    "name": "FDMS Transaction Log",
                    "label": _("FDMS Transaction Log"),
                    "description": _("View audit logs for FDMS transactions."),
                },
                {
                    "type": "doctype",
                    "name": "Compliance Report",
                    "label": _("Compliance Report"),
                    "description": _("Review generated FDMS compliance reports."),
                },
            ],
        }
    ]
