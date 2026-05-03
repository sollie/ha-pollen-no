"""Tests for api.py."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.pollen_no.api import (
    PollenDataAPI,
    PollenDataAPIConnectionError,
    PollenDataAPIError,
    PollenDataAPITimeoutError,
    build_base_url,
)


class TestBuildBaseUrl:
    def test_bare_host(self):
        assert build_base_url("localhost:8080") == "http://localhost:8080"

    def test_http_scheme(self):
        assert build_base_url("http://myserver.com") == "http://myserver.com"

    def test_https_scheme(self):
        assert build_base_url("https://myserver.com:443") == "https://myserver.com:443"

    def test_trailing_slash_stripped(self):
        assert build_base_url("http://localhost:8080/") == "http://localhost:8080"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            build_base_url("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            build_base_url("   ")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="too long"):
            build_base_url("a" * 254)

    def test_bad_scheme_raises(self):
        with pytest.raises(ValueError, match="scheme"):
            build_base_url("ftp://host.com")


def _make_api(mock_session=None):
    if mock_session is None:
        mock_session = MagicMock()
    return PollenDataAPI(hostname="http://localhost:8080", session=mock_session)


def _mock_response(status: int, json_data=None, text_data: str = ""):
    response = AsyncMock()
    response.status = status
    response.json = AsyncMock(return_value=json_data)
    response.text = AsyncMock(return_value=text_data)
    return response


class TestPollenDataAPIRequest:
    async def test_successful_json_response(self):
        api = _make_api()
        resp = _mock_response(200, json_data=["oslo"])
        api.session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=resp),
            __aexit__=AsyncMock(return_value=False),
        ))
        with patch("async_timeout.timeout", return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=None),
            __aexit__=AsyncMock(return_value=False),
        )):
            result = await api._request("/regions")
        assert result == ["oslo"]

    async def test_non_200_raises_api_error(self):
        api = _make_api()
        resp = _mock_response(500, text_data="server error")
        api.session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=resp),
            __aexit__=AsyncMock(return_value=False),
        ))
        with patch("async_timeout.timeout", return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=None),
            __aexit__=AsyncMock(return_value=False),
        )):
            with pytest.raises(PollenDataAPIError, match="500"):
                await api._request("/regions")

    async def test_timeout_raises_timeout_error(self):
        api = _make_api()
        with patch("async_timeout.timeout", side_effect=asyncio.TimeoutError):
            with pytest.raises(PollenDataAPITimeoutError):
                await api._request("/regions")

    async def test_client_error_raises_connection_error(self):
        api = _make_api()
        with patch("async_timeout.timeout", return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=None),
            __aexit__=AsyncMock(return_value=False),
        )):
            api.session.get = MagicMock(side_effect=aiohttp.ClientError("conn fail"))
            with pytest.raises(PollenDataAPIConnectionError):
                await api._request("/regions")


class TestGetRegions:
    async def test_list_response(self):
        api = _make_api()
        api._request = AsyncMock(return_value=["oslo", "bergen"])
        result = await api.get_regions()
        assert result == ["oslo", "bergen"]

    async def test_dict_response_with_regions_key(self):
        api = _make_api()
        api._request = AsyncMock(return_value={"regions": ["oslo"]})
        result = await api.get_regions()
        assert result == ["oslo"]

    async def test_unexpected_format_returns_empty(self):
        api = _make_api()
        api._request = AsyncMock(return_value="not-a-list")
        result = await api.get_regions()
        assert result == []


class TestGetPollenData:
    async def test_date_keyed_response(self):
        api = _make_api()
        api._request = AsyncMock(return_value={
            "2026-05-03": {"bjork": 3, "gress": 0},
            "2026-05-04": {"bjork": 2, "gress": 1},
        })
        result = await api.get_pollen_data("oslo")
        assert result == {
            "2026-05-03": {"bjork": 3, "gress": 0},
            "2026-05-04": {"bjork": 2, "gress": 1},
        }

    async def test_non_dict_response_returns_empty(self):
        api = _make_api()
        api._request = AsyncMock(return_value=[])
        result = await api.get_pollen_data("oslo")
        assert result == {}

    async def test_skips_non_dict_day_values(self):
        api = _make_api()
        api._request = AsyncMock(return_value={"2026-05-03": "bad"})
        result = await api.get_pollen_data("oslo")
        assert result == {}


class TestGetForecast:
    async def test_string_response(self):
        api = _make_api()
        api._request = AsyncMock(return_value="High birch pollen")
        result = await api.get_forecast("oslo")
        assert result == "High birch pollen"

    async def test_region_keyed_dict(self):
        api = _make_api()
        api._request = AsyncMock(return_value={"oslo": "Low pollen", "bergen": "High pollen"})
        result = await api.get_forecast("oslo")
        assert result == "Low pollen"

    async def test_dict_with_forecast_key_fallback(self):
        api = _make_api()
        api._request = AsyncMock(return_value={"forecast": "Low pollen"})
        result = await api.get_forecast("oslo")
        assert result == "Low pollen"

    async def test_api_error_returns_none(self):
        api = _make_api()
        api._request = AsyncMock(side_effect=PollenDataAPIError("fail"))
        result = await api.get_forecast("oslo")
        assert result is None

    async def test_missing_key_returns_none(self):
        api = _make_api()
        api._request = AsyncMock(return_value={"other": "data"})
        result = await api.get_forecast("oslo")
        assert result is None


class TestGetCombinedData:
    async def test_full_response(self):
        api = _make_api()
        api._request = AsyncMock(return_value={
            "pollen": {
                "2026-05-03": {"bjork": 3, "gress": 0},
                "2026-05-04": {"bjork": 2, "gress": 1},
            },
            "forecast": {"oslo": "Some text"},
            "last_updated": "2025-04-15T10:00:00Z",
        })
        result = await api.get_combined_data("oslo")
        assert result["pollen"] == {
            "2026-05-03": {"bjork": 3, "gress": 0},
            "2026-05-04": {"bjork": 2, "gress": 1},
        }
        assert result["forecast"] == "Some text"
        assert result["last_updated"] == "2025-04-15T10:00:00Z"

    async def test_forecast_string_passthrough(self):
        api = _make_api()
        api._request = AsyncMock(return_value={
            "pollen": {},
            "forecast": "Plain string forecast",
        })
        result = await api.get_combined_data("oslo")
        assert result["forecast"] == "Plain string forecast"

    async def test_non_dict_returns_empty(self):
        api = _make_api()
        api._request = AsyncMock(return_value="bad")
        result = await api.get_combined_data("oslo")
        assert result == {}

    async def test_level_0_preserved(self):
        api = _make_api()
        api._request = AsyncMock(return_value={
            "pollen": {"2026-05-03": {"gress": 0}},
            "forecast": {},
        })
        result = await api.get_combined_data("oslo")
        assert result["pollen"]["2026-05-03"]["gress"] == 0


class TestTestConnection:
    async def test_returns_true_on_success(self):
        api = _make_api()
        api.get_regions = AsyncMock(return_value=["oslo"])
        assert await api.test_connection() is True

    async def test_returns_false_on_error(self):
        api = _make_api()
        api.get_regions = AsyncMock(side_effect=PollenDataAPIConnectionError("fail"))
        assert await api.test_connection() is False
