from pydantic import BaseModel
from typing import Optional


class DeviceInfo(BaseModel):
    type: str
    family: str
    brand: str
    model: str


class OSInfo(BaseModel):
    family: str
    version: str


class BrowserInfo(BaseModel):
    family: str
    version: str


class ClientInfo(BaseModel):
    device: DeviceInfo
    os: OSInfo
    browser: BrowserInfo
    ua_string: str
    raw: str


class NetworkInfo(BaseModel):
    ip: str
    forwarded: Optional[str] = None
    origin: Optional[str] = None
    referer: Optional[str] = None


class AcceptHeaders(BaseModel):
    accept: Optional[str] = None
    accept_encoding: Optional[str] = None
    accept_language: Optional[str] = None


class FetchMetadata(BaseModel):
    sec_fetch_site: Optional[str] = None
    sec_fetch_mode: Optional[str] = None
    sec_fetch_dest: Optional[str] = None


class MiscInfo(BaseModel):
    dnt: Optional[str] = None


class SessionInfo(BaseModel):
    network: NetworkInfo
    client: ClientInfo
    accept_headers: AcceptHeaders
    fetch_metadata: FetchMetadata
    misc: MiscInfo
