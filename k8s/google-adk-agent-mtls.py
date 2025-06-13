#!/usr/bin/env python3
"""
Modified Google ADK agent with mTLS support for Kubernetes deployment
"""

import logging
import os
import ssl

import click

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent import ReimbursementAgent
from agent_executor import ReimbursementAgentExecutor
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""
    pass


def create_server_ssl_context():
    """Create SSL context for server with client certificate verification"""
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    
    # Server certificate and key from Kubernetes secret
    cert_file = os.environ.get('TLS_CERT_FILE', '/etc/tls/google-adk-agent/tls.crt')
    key_file = os.environ.get('TLS_KEY_FILE', '/etc/tls/google-adk-agent/tls.key')
    ca_file = os.environ.get('TLS_CA_FILE', '/etc/tls/ca/ca.crt')
    
    context.load_cert_chain(certfile=cert_file, keyfile=key_file)
    
    # CA certificate for client verification
    context.load_verify_locations(ca_file)
    context.verify_mode = ssl.CERT_REQUIRED
    
    return context


@click.command()
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=10002)
@click.option('--enable-mtls', default=False, is_flag=True, help='Enable mTLS authentication')
def main(host, port, enable_mtls):
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'TRUE':
            if not os.getenv('GOOGLE_API_KEY'):
                raise MissingAPIKeyError(
                    'GOOGLE_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE.'
                )

        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id='process_reimbursement',
            name='Process Reimbursement Tool',
            description='Helps with the reimbursement process for users given the amount and purpose of the reimbursement.',
            tags=['reimbursement'],
            examples=[
                'Can you reimburse me $20 for my lunch with the clients?'
            ],
        )
        
        # Update agent card URL based on mTLS setting
        protocol = 'https' if enable_mtls else 'http'
        agent_card = AgentCard(
            name='Reimbursement Agent',
            description='This agent handles the reimbursement process for the employees given the amount and purpose of the reimbursement.',
            url=f'{protocol}://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=ReimbursementAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=ReimbursementAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        
        request_handler = DefaultRequestHandler(
            agent_executor=ReimbursementAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )
        
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )
        
        import uvicorn

        if enable_mtls:
            logger.info(f'Starting Google ADK Agent with mTLS on https://{host}:{port}')
            ssl_context = create_server_ssl_context()
            uvicorn.run(server.build(), host=host, port=port, ssl_context=ssl_context)
        else:
            logger.info(f'Starting Google ADK Agent on http://{host}:{port}')
            uvicorn.run(server.build(), host=host, port=port)
            
    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)


if __name__ == '__main__':
    main()
