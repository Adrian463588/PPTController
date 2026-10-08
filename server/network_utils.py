import socket
import io
import base64
import qrcode

def get_local_ip() -> str:
    """Finds the most appropriate local network IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to public DNS server to find outbound route without sending packets
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def get_all_local_ips() -> list[str]:
    """Retrieves all non-loopback IPv4 addresses."""
    ips = set()
    try:
        primary = get_local_ip()
        if primary and primary != '127.0.0.1':
            ips.add(primary)
        
        hostname = socket.gethostname()
        for addr_info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = addr_info[4][0]
            if not ip.startswith('127.'):
                ips.add(ip)
    except Exception:
        pass
    
    res = list(ips)
    if not res:
        res = ['127.0.0.1']
    return res

def generate_qr_base64(data: str) -> str:
    """Generates a QR code and returns it as a base64 encoded PNG string."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def generate_terminal_qr(data: str, border: int = 2) -> str:
    """Generates an ANSI-colored high-contrast terminal-friendly QR code string.

    Uses half-block unicode characters (▀, ▄, █, ' ') with explicit white background
    (\\x1b[47m) and black foreground (\\x1b[30m) ANSI escapes to ensure a solid quiet
    zone and reliable smartphone camera recognition without cutoffs on all terminals.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    # Ensure even number of rows for 2-row half-block character pairs
    if len(matrix) % 2 != 0:
        matrix.append([False] * len(matrix[0]))

    lines = []
    for r in range(0, len(matrix), 2):
        top_row = matrix[r]
        bot_row = matrix[r + 1]
        line_chars = ["\x1b[47m\x1b[30m"]
        for c in range(len(top_row)):
            top = top_row[c]
            bot = bot_row[c]
            if top and bot:
                line_chars.append("█")
            elif top and not bot:
                line_chars.append("▀")
            elif not top and bot:
                line_chars.append("▄")
            else:
                line_chars.append(" ")
        line_chars.append("\x1b[0m")
        lines.append("".join(line_chars))

    return "\n".join(lines)

def print_terminal_qr(data: str):
    """Outputs an ANSI high-contrast QR code directly into the terminal."""
    try:
        qr_str = generate_terminal_qr(data)
        print("\n--- SCAN TO CONNECT ---")
        print(qr_str)
        print(f"URL: {data}\n")
    except Exception:
        print(f"URL: {data}")

