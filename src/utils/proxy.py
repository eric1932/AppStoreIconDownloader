import os

ALL_PROXY: str = os.getenv('all_proxy')
PROXY_PROTO, PROXY_HOST_PORT = ALL_PROXY.split("://") if ALL_PROXY else (None, None)
PROXY_HOST, PROXY_PORT = PROXY_HOST_PORT.split(":") if PROXY_HOST_PORT else (None, 0)

# def use_system_proxy() -> None:
#     if PROXY_PROTO and PROXY_HOST and PROXY_PORT:
#         port = 0
#         try:
#             port = int(PROXY_PORT)
#         except ValueError:
#             pass
#         socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, port)
#     socket.socket = socks.socksocket
