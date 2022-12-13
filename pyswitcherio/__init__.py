import sys

import time
import binascii
import logging
from bleak.backends.device import BLEDevice
import asyncio
from bleak import BleakScanner
from bleak import BleakClient
from bleak_retry_connector import (
    BLEAK_RETRY_EXCEPTIONS,
    BleakClientWithServiceCache,
    BleakNotFoundError,
    ble_device_has_changed,
    establish_connection,
)
DEFAULT_RETRY_COUNT = 5
DEFAULT_RETRY_TIMEOUT = 1

ON_KEY1 = binascii.a2b_hex("00")
OFF_KEY1 = binascii.a2b_hex("01")

ON_KEY2 = binascii.a2b_hex("05")
OFF_KEY2 = binascii.a2b_hex("03")
# 1구의 경우 00,01
# 2구의 경우 05,03

UUID = "0000150b-0000-1000-8000-00805f9b34fb"


_LOGGER = logging.getLogger(__name__)


class IOSwitcher:
    def __init__(self, mac, device: BLEDevice, type=1,  **kwargs) -> None:
        """IO 스위쳐 초기화."""
        self._mac = mac.lower()
        #self._device: BLEDevice | None = None
        if device is None:
            self._device = asyncio.run(
                BleakScanner.find_device_by_address(self._mac))
        else:
            self._device = device
        self._client: BleakClient | None = None
        self._char_uuid = None
        self._retry_count = DEFAULT_RETRY_COUNT
        if type == 2:
            self._on_key = ON_KEY2
            self._off_key = OFF_KEY2
        else:
            self._on_key = ON_KEY1
            self._off_key = OFF_KEY1

    async def _connect(self) -> None:
        if self._client is not None and self._client.is_connected():
            return
        try:
            _LOGGER.debug("스위쳐 연결 중")
            self._client = BleakClient(self._device, self._disconnected)

            await self._client.connect()

            services = await self._client.get_services()
            for service in services:
                if service.uuid == UUID:
                    self._char_uuid = service.characteristics[0].uuid

            _LOGGER.debug("스위쳐 연결 완료!")
        except Exception as e:
            _LOGGER.debug("스위쳐 연결 실패", e, exc_info=True)
            self._client = None
            raise

    async def _disconnect(self) -> None:
        if self._client is None:
            return
        _LOGGER.debug("연결 끊기 완료")
        try:
            await self._client.disconnect()
        except Exception as e:
            _LOGGER.warning("연결을 끊는중 에러 발생", e, exc_info=True)
        finally:
            self._client = None

    async def turn_on(self) -> bool:
        """불을 켭니다."""
        return await self._sendcommand(self._on_key, self._retry_count)

    async def turn_off(self) -> bool:
        """불을 끕니다."""
        return await self._sendcommand(self._off_key, self._retry_count)

    def _commandkey(self, key) -> str:
        # 여기다 타입별로 명령어 추가
        return key

    async def _sendcommand(self, key, retry) -> bool:
        send_success = False
        command = self._commandkey(key)
        try:
            await self._connect()
            send_success = await self._writekey(command)
        except Exception as e:
            _LOGGER.warning(e, exc_info=True)
        finally:
            await self._disconnect()
        if send_success:
            return True
        if retry < 1:
            _LOGGER.error(
                "스위쳐 통신 실패..", exc_info=True
            )
            return False
        _LOGGER.warning("스위쳐 연결 실패. 다시 시도 남은 횟수 %d", retry)
        asyncio.sleep(DEFAULT_RETRY_TIMEOUT)
        return await self._sendcommand(key, retry - 1)

    async def _writekey(self, key) -> bool:
        if self._char_uuid is None:
            _LOGGER.error("캐릭터리스틱 UUID가 없습니다.")
            return False

        _LOGGER.debug("키 보내는중, %s", key)
        await self._client.write_gatt_char(self._char_uuid, key)

        return True

    async def run(self):

        devices = await BleakScanner.discover()
    # 검색된 장치들 리스트 출력
        for d in devices:
            print(d)
            print(d.address)

    def _disconnected(self, client: BleakClientWithServiceCache) -> None:
        """Disconnected callback."""
        if self._expected_disconnect:
            _LOGGER.debug(
                "%s: Disconnected from device; mac: %s", self.name, self._mac
            )
            return
        _LOGGER.warning(
            "%s: Device unexpectedly disconnected; mac: %s",
            self.name,
            self._mac,
        )

    @property
    def name(self) -> str:
        """Return device name."""
        return f"{self._device.name} ({self._device.address})"


if __name__ == "__main__":
    switcher = IOSwitcher("xx:xx:xx:xx:xx:xx", None, 1)
    # asyncio.run(switcher.run())
    asyncio.run(switcher.turn_on())
