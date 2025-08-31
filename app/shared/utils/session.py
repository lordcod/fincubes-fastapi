from fastapi import Request
from user_agents import parse

from app.schemas.misc.session import (
    DeviceInfo,
    OSInfo,
    BrowserInfo,
    ClientInfo,
    NetworkInfo,
    AcceptHeaders,
    FetchMetadata,
    MiscInfo,
    SessionInfo
)


def detect_device(user_agent: str) -> ClientInfo:
    ua = parse(user_agent)

    rules = [
        (ua.is_mobile, "mobile"),
        (ua.is_tablet, "tablet"),
        (ua.is_pc, "desktop"),
        (ua.is_bot, "bot"),
    ]
    device_type = next((label for cond, label in rules if cond), "unknown")

    return ClientInfo(
        device=DeviceInfo(
            type=device_type,
            family=ua.device.family or "unknown",
            brand=ua.device.brand or "unknown",
            model=ua.device.model or "unknown",
        ),
        os=OSInfo(
            family=ua.os.family or "unknown",
            version=ua.os.version_string or "unknown",
        ),
        browser=BrowserInfo(
            family=ua.browser.family or "unknown",
            version=ua.browser.version_string or "unknown",
        ),
        ua_string=str(ua),
        raw=user_agent,
    )


def get_session_info(request: Request) -> SessionInfo:
    headers = request.headers

    network = NetworkInfo(
        ip=request.client.host,
        forwarded=headers.get("X-Forwarded-For"),
        origin=headers.get("origin"),
        referer=headers.get("referer"),
    )

    user_agent = headers.get("user-agent", "")
    client_info = detect_device(user_agent)

    accept_headers = AcceptHeaders(
        accept=headers.get("accept"),
        accept_encoding=headers.get("accept-encoding"),
        accept_language=headers.get("accept-language"),
    )

    fetch_metadata = FetchMetadata(
        sec_fetch_site=headers.get("sec-fetch-site"),
        sec_fetch_mode=headers.get("sec-fetch-mode"),
        sec_fetch_dest=headers.get("sec-fetch-dest"),
    )

    misc = MiscInfo(
        dnt=headers.get("dnt")
    )

    return SessionInfo(
        network=network,
        client=client_info,
        accept_headers=accept_headers,
        fetch_metadata=fetch_metadata,
        misc=misc,
    )
