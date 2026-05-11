from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
	long_description = fh.read()

setup(
	name="verityfiscal",
	version="1.0.0",
	author="VERITYFiscal",
	author_email="support@verityfiscal.com",
	description="ERPNext FDMS Integration for Virtual Fiscalisation - ZIMRA Compliant",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/Vickella/verityfiscal",
	packages=find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
		"Operating System :: OS Independent",
		"Intended Audience :: Developers",
		"Topic :: Office/Business :: Financial :: Point-Of-Sale",
	],
	python_requires=">=3.8",
	install_requires=[
		"frappe-bench",
		"requests>=2.25.0",
		"cryptography>=3.4.8",
		"qrcode>=7.3.1",
	],
	extras_require={
		"dev": ["pytest", "black", "flake8"],
	},
)
