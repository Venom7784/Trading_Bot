import time
import hmac
import hashlib
import json

def _now_ts() -> str:
    return str(int(time.time()))

def sign_request(
    secret: str,
    method: str,
    timestamp: str,
    path: str,
    query: str,
    payload: str
) -> str:
    msg = (method + timestamp + path + query + payload).encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()

def signed_headers(
    api_key: str,
    api_secret: str,
    method: str,
    path: str,
    payload: dict | None = None,
    query: str = ""
) -> dict:
    ts = _now_ts()
    payload_str = json.dumps(payload) if payload else ""
    sig = sign_request(api_secret, method.upper(), ts, path, query, payload_str)

    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "api-key": api_key,
        "timestamp": ts,
        "signature": sig
    }

def signed_headers_wallet(
    api_key: str,
    api_secret: str,
    method: str,
    path: str,
    payload: dict | None = None,
    query: str = ""
) -> dict:
    ts = _now_ts()
    payload_str = json.dumps(payload) if payload else ""
    sig = sign_request(api_secret, method.upper(), ts, path, query, payload_str)

    return {
        "Accept": "application/json",
        "api-key": api_key,
        "timestamp": ts,
        "signature": sig
    }
