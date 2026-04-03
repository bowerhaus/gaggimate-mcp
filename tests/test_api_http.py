"""Tests for HTTP client with HTML detection and retry logic."""

import struct
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiohttp import ClientError

from gaggimate_mcp.api.http import (
    GaggimateHTTPClient,
    _is_html_response,
    MAX_RETRIES,
)
from gaggimate_mcp.config import GaggimateConfig
from gaggimate_mcp.errors import GaggimateError, ErrorCode


# --- _is_html_response tests ---


class TestIsHtmlResponse:
    """Tests for HTML response detection."""

    def test_detects_doctype_lowercase(self):
        assert _is_html_response(b'<!doctype html><html>...') is True

    def test_detects_doctype_uppercase(self):
        assert _is_html_response(b'<!DOCTYPE html><html>...') is True

    def test_detects_html_tag_lowercase(self):
        assert _is_html_response(b'<html><head>...') is True

    def test_detects_html_tag_uppercase(self):
        assert _is_html_response(b'<HTML><HEAD>...') is True

    def test_rejects_binary_shot_data(self):
        # Valid SHOT magic bytes
        data = struct.pack('<I', 0x544F4853) + b'\x00' * 124
        assert _is_html_response(data) is False

    def test_rejects_empty_data(self):
        assert _is_html_response(b'') is False

    def test_rejects_short_data(self):
        assert _is_html_response(b'abc') is False

    def test_rejects_random_binary(self):
        assert _is_html_response(b'\x00\x01\x02\x03\x04\x05') is False

    def test_firmware_1_8_0_html_magic_bytes(self):
        """The specific bytes from the firmware 1.8.0 error report."""
        # 0x6f64213c in little-endian = bytes 3c 21 64 6f = "<!do"
        data = struct.pack('<I', 0x6f64213c) + b'ctype html>' + b'\x00' * 100
        assert _is_html_response(data) is True


# --- Helper to build a minimal valid shot binary ---

def _build_valid_shot_binary(shot_id="000001"):
    """Build minimal valid V4 shot binary for testing."""
    magic = 0x544F4853
    version = 4
    header = struct.pack(
        '<IB B H H H I I I I 32s 48s H',
        magic, version, 0, 128,
        100, 0,
        0b11, 2, 20000, 1640000000,
        b'test\x00' + b'\x00' * 27,
        b'Test\x00' + b'\x00' * 43,
        360,
    )
    header = header + b'\x00' * (128 - len(header))
    samples = struct.pack('<HH', 10, 900) + struct.pack('<HH', 20, 920)
    return header + samples


# --- HTTP client tests ---


class TestHTTPClientConfig:
    """Tests for HTTP client configuration."""

    def test_uses_config_timeout(self):
        config = GaggimateConfig(gaggimate_host="test.local", request_timeout=20.0)
        client = GaggimateHTTPClient(config)
        assert client.timeout.total == 20.0

    def test_default_timeout_is_15(self):
        config = GaggimateConfig(gaggimate_host="test.local")
        client = GaggimateHTTPClient(config)
        assert client.timeout.total == 15.0


class TestFetchShotHTMLDetection:
    """Tests for HTML response detection in fetch_shot."""

    @pytest.fixture
    def config(self):
        return GaggimateConfig(gaggimate_host="test.local", request_timeout=1.0)

    @pytest.fixture
    def client(self, config):
        return GaggimateHTTPClient(config)

    @pytest.mark.asyncio
    async def test_html_response_raises_retryable_error(self, client):
        """HTML response should raise a retryable GaggimateError."""
        html_body = b'<!DOCTYPE html><html><body>Error</body></html>'

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=html_body)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(GaggimateError) as exc_info:
                    await client.fetch_shot("000195")

        assert exc_info.value.code == ErrorCode.PARSE_ERROR
        assert "HTML" in exc_info.value.message
        assert exc_info.value.retryable is True

    @pytest.mark.asyncio
    async def test_valid_binary_parses_successfully(self, client):
        """Valid binary shot data should parse without error."""
        binary_data = _build_valid_shot_binary()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=binary_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await client.fetch_shot("000001")

        assert result is not None
        assert result.id == "000001"

    @pytest.mark.asyncio
    async def test_404_returns_none(self, client):
        """404 response should return None without retrying."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await client.fetch_shot("999999")

        assert result is None


class TestFetchShotRetry:
    """Tests for retry logic in fetch_shot."""

    @pytest.fixture
    def config(self):
        return GaggimateConfig(gaggimate_host="test.local", request_timeout=1.0)

    @pytest.fixture
    def client(self, config):
        return GaggimateHTTPClient(config)

    @pytest.mark.asyncio
    async def test_retries_on_html_then_succeeds(self, client):
        """Should retry on HTML response and succeed when binary is returned."""
        html_body = b'<!DOCTYPE html><html><body>Error</body></html>'
        binary_data = _build_valid_shot_binary()

        call_count = 0

        async def mock_read():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return html_body
            return binary_data

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = mock_read
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await client.fetch_shot("000001")

        assert result is not None
        assert result.id == "000001"
        assert call_count == 2
        mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_retries_exhausted_raises(self, client):
        """Should raise after exhausting all retries."""
        html_body = b'<!DOCTYPE html><html><body>Error</body></html>'

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=html_body)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(GaggimateError) as exc_info:
                    await client.fetch_shot("000195")

        assert exc_info.value.code == ErrorCode.PARSE_ERROR
        assert exc_info.value.retryable is True

    @pytest.mark.asyncio
    async def test_non_retryable_error_not_retried(self, client):
        """Non-retryable errors should not be retried."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.reason = "Internal Server Error"
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(GaggimateError) as exc_info:
                await client.fetch_shot("000001")

        assert exc_info.value.code == ErrorCode.API_ERROR

    @pytest.mark.asyncio
    async def test_timeout_is_retryable(self, client):
        """Timeout errors should be retried."""
        call_count = 0
        binary_data = _build_valid_shot_binary()

        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise asyncio.TimeoutError()
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.read = AsyncMock(return_value=binary_data)
            mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_resp.__aexit__ = AsyncMock(return_value=False)
            return mock_resp

        mock_session = AsyncMock()
        mock_session.get = MagicMock(side_effect=mock_get)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await client.fetch_shot("000001")

        assert result is not None
        assert call_count == 2
