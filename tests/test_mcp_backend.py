from src.services.mcp_backend.server import build_server


def test_mcp_server_builder_exists():
    assert callable(build_server)

