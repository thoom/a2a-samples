#!/usr/bin/env python3
"""
Modified demo UI main.py with mTLS support for Kubernetes deployment
"""

import os
import ssl
import httpx
from contextlib import asynccontextmanager

import mesop as me

from components.api_key_dialog import api_key_dialog
from components.page_scaffold import page_scaffold
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from pages.agent_list import agent_list_page
from pages.conversation import conversation_page
from pages.event_list import event_list_page
from pages.home import home_page_content
from pages.settings import settings_page_content
from pages.task_list import task_list_page
from service.server.server import ConversationServer
from state import host_agent_service
from state.state import AppState


load_dotenv()


def create_server_ssl_context():
    """Create SSL context for server with client certificate verification"""
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    
    # Server certificate and key from Kubernetes secret
    cert_file = os.environ.get('TLS_CERT_FILE', '/etc/tls/demo-ui/tls.crt')
    key_file = os.environ.get('TLS_KEY_FILE', '/etc/tls/demo-ui/tls.key')
    ca_file = os.environ.get('TLS_CA_FILE', '/etc/tls/ca/ca.crt')
    
    context.load_cert_chain(certfile=cert_file, keyfile=key_file)
    
    # CA certificate for client verification
    context.load_verify_locations(ca_file)
    context.verify_mode = ssl.CERT_REQUIRED
    
    return context


def create_client_ssl_context():
    """Create SSL context for client requests with mTLS"""
    context = ssl.create_default_context()
    
    # Client certificate and key for making requests to other services
    cert_file = os.environ.get('TLS_CERT_FILE', '/etc/tls/demo-ui/tls.crt')
    key_file = os.environ.get('TLS_KEY_FILE', '/etc/tls/demo-ui/tls.key')
    ca_file = os.environ.get('TLS_CA_FILE', '/etc/tls/ca/ca.crt')
    
    context.load_cert_chain(certfile=cert_file, keyfile=key_file)
    context.load_verify_locations(ca_file)
    
    return context


# ...existing mesop page definitions...
def on_load(e: me.LoadEvent):
    """On load event"""
    state = me.state(AppState)
    me.set_theme_mode(state.theme_mode)
    if 'conversation_id' in me.query_params:
        state.current_conversation_id = me.query_params['conversation_id']
    else:
        state.current_conversation_id = ''

    uses_vertex_ai = (
        os.getenv('GOOGLE_GENAI_USE_VERTEXAI', '').upper() == 'TRUE'
    )
    api_key = os.getenv('GOOGLE_API_KEY', '')

    if uses_vertex_ai:
        state.uses_vertex_ai = True
    elif api_key:
        state.api_key = api_key
    else:
        state.api_key_dialog_open = True


security_policy = me.SecurityPolicy(
    allowed_script_srcs=[
        'https://cdn.jsdelivr.net',
    ]
)


@me.page(path='/', title='Chat', on_load=on_load, security_policy=security_policy)
def home_page():
    """Main Page"""
    state = me.state(AppState)
    api_key_dialog()
    with page_scaffold():
        home_page_content(state)


# ...existing other page definitions...


class HTTPXClientWrapper:
    """Wrapper to return the singleton client with mTLS support"""

    async_client: httpx.AsyncClient = None

    def start(self):
        """Instantiate the client with mTLS support"""
        enable_mtls = os.environ.get('ENABLE_MTLS', 'false').lower() == 'true'
        
        if enable_mtls:
            # mTLS configuration
            cert_file = os.environ.get('TLS_CERT_FILE', '/etc/tls/demo-ui/tls.crt')
            key_file = os.environ.get('TLS_KEY_FILE', '/etc/tls/demo-ui/tls.key')
            ca_file = os.environ.get('TLS_CA_FILE', '/etc/tls/ca/ca.crt')
            
            self.async_client = httpx.AsyncClient(
                timeout=30,
                verify=ca_file,
                cert=(cert_file, key_file)
            )
        else:
            # Standard HTTP client
            self.async_client = httpx.AsyncClient(timeout=30)

    async def stop(self):
        """Gracefully shutdown"""
        await self.async_client.aclose()
        self.async_client = None

    def __call__(self):
        """Calling the instantiated HTTPXClientWrapper returns the wrapped singleton"""
        assert self.async_client is not None
        return self.async_client


# Setup the server global objects
httpx_client_wrapper = HTTPXClientWrapper()
agent_server = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    httpx_client_wrapper.start()
    agent_server = ConversationServer(app, httpx_client_wrapper())
    app.openapi_schema = None
    app.mount(
        '/',
        WSGIMiddleware(
            me.create_wsgi_app(
                debug_mode=os.environ.get('DEBUG_MODE', '') == 'true'
            )
        ),
    )
    app.setup()
    yield
    await httpx_client_wrapper.stop()


if __name__ == '__main__':
    import uvicorn

    app = FastAPI(lifespan=lifespan)

    # Setup the connection details
    host = os.environ.get('A2A_UI_HOST', '0.0.0.0')
    port = int(os.environ.get('A2A_UI_PORT', '12000'))
    enable_mtls = os.environ.get('ENABLE_MTLS', 'false').lower() == 'true'

    # Set the client to talk to the server
    if enable_mtls:
        host_agent_service.server_url = f'https://{host}:{port}'
    else:
        host_agent_service.server_url = f'http://{host}:{port}'

    if enable_mtls:
        ssl_context = create_server_ssl_context()
        uvicorn.run(
            app,
            host=host,
            port=port,
            ssl_context=ssl_context,
            timeout_graceful_shutdown=0,
        )
    else:
        uvicorn.run(
            app,
            host=host,
            port=port,
            timeout_graceful_shutdown=0,
        )
