from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, Optional


class ProtectionRequest(BaseModel):
    server_nonce: str = Field(...,
                              description="Nonce, выданный сервером (base64/hex)")
    nonce: str = Field(..., description="Клиентский nonce (base64/hex)")
    fingerprint: str = Field(...,
                             description="Браузерный/устройственный fingerprint")
    dpop: str = Field(..., description="DPoP‑JWT согласно RFC 9449")
    jwk: Dict[str, Any] = Field(
        ...,
        description="Публичный JWK (формат RFC 7517)"
    )
    turnstile: Optional[str] = Field(...,
                                     description="Токен Cloudflare Turnstile")

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "server_nonce": "bG9yZW0gaXBz...",
                "nonce": "Z3VzdGF2aX...",
                "fingerprint": "a9f6c73c5b2e4d1f9d0...",
                "dpop": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEyMyJ9...",
                "jwk": {
                    "kty": "EC",
                    "crv": "P-256",
                    "x": "f83OJ3D2xF4...",
                    "y": "x_FEzRu9YO..."
                },
                "turnstile": "0x4AAAAAAA..."
            }
        }
    )
