import requests
from django.http import JsonResponse


# https://dashboard.ipdata.co/index.html

# Replace with your real API key
IPDATA_API_KEY = '496d4cb8026d3edef794719a68aee4a8f5aa7ba513ee37eabc14df65'

def get_client_ip(request):
    """Get client IP even if behind proxy/load balancer"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class VPNBlockerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        print("[VPNBlocker] Middleware initialized.")

    def __call__(self, request):
        client_ip = get_client_ip(request)
        print(f"[VPNBlocker] Incoming request IP: {client_ip}")

        # Skip localhost or private IPs
        if client_ip.startswith("127.") or client_ip == "::1" or client_ip.startswith("192.168."):
            print(f"[VPNBlocker] Skipping local/private IP: {client_ip}")
            return self.get_response(request)

        try:
            # Request to ipdata VPN check API
            url = f"https://api.ipdata.co/{client_ip}?api-key={IPDATA_API_KEY}"
            print(f"[VPNBlocker] Querying: {url}")
            response = requests.get(url, timeout=3)
            data = response.json()
            print(f"[VPNBlocker] API response for {client_ip}: {data}")

            threat = data.get("threat", {})
            is_vpn = threat.get("is_vpn", False)
            is_proxy = threat.get("is_proxy", False)
            is_tor = threat.get("is_tor", False)
            print(f"[VPNBlocker] Threat info: vpn={is_vpn}, proxy={is_proxy}, tor={is_tor}")

            if is_vpn or is_proxy or is_tor:
                print(f"[VPNBlocker] BLOCKED: {client_ip} (VPN/Proxy/Tor detected)")
                return JsonResponse({
                    "detail": "Access denied: VPN/Proxy/Tor usage detected."
                }, status=403)

        except Exception as e:
            print(f"[VPNBlocker] API error: {e}")

        print(f"[VPNBlocker] ALLOWED: {client_ip}")
        return self.get_response(request)
