# -*- coding: utf-8 -*-

"""Application constants loaded from environment variables (XMPP credentials)."""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on environment variables being set

SERVICE_XMPP_UID = os.environ.get('SERVICE_XMPP_UID', '')
SERVICE_XMPP_PASS = os.environ.get('SERVICE_XMPP_PASS', '')
XMPP_UID = os.environ.get('XMPP_UID', '')
