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

def print_terminal_qr(data: str):
    """Outputs an ASCII QR code directly into the terminal."""
    try:
        qr = qrcode.QRCode(version=1, box_size=1, border=1)
        qr.add_data(data)
        qr.make(fit=True)
        print("\n--- SCAN TO CONNECT ---")
        qr.print_ascii(invert=True)
        print(f"URL: {data}\n")
    except Exception as e:
        print(f"URL: {data}")
