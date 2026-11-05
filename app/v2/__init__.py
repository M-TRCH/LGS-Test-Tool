"""LGS Test Tool v2.0: JSON API + plain HTML/CSS/JS front end, mounted at /v2.

Runs inside the same process and port as the NiceGUI pages (the one Modbus
worker, the one login gate, the one data folder), so v1.9.x keeps working at
/ while v2 is built up page by page. Nothing here may talk to a gateway except
through short, bounded, closed-again connections: a gateway has two client
slots and a soak holds one of them.
"""
