"""TLS verificado com as autoridades certificadoras confiáveis do sistema."""

import ssl


def system_tls_context() -> ssl.SSLContext:
    return ssl.create_default_context()
