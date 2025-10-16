from . import server

def main():
    server.mcp.run()

__version__ = "0.1.0"
__all__ = ['main', 'server']
