import webbrowser
import urllib.parse

FRONTEND_BASE = "https://upon-overeater-robust.ngrok-free.dev"

def send_message(mobile: str, plate: str, violation: str, fine: int):

    payment_link = f"{FRONTEND_BASE}/pay?plate={plate}&fine={fine}&mobile={mobile}"

    message = f"""🚓 Traffic Police eChallan

Vehicle: {plate}
Violation: {violation}
Fine: ₹{fine}

Pay here:
{payment_link}
"""

    encoded_msg = urllib.parse.quote(message)

    url = f"https://wa.me/91{mobile}?text={encoded_msg}"

    webbrowser.open(url)