import socket

from app.dev_server import port_is_available


def test_port_is_available_for_unused_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    assert port_is_available(port) is True


def test_port_is_unavailable_while_bound():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]

        assert port_is_available(port) is False