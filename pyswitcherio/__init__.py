import sys

import time
import binascii
import logging
from bleak import BleakClient
import asyncio
from bleak import BleakScanner
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
    def __init__(self, mac, type=1, **kwargs) -> None:
        """IO 스위쳐 초기화."""
        self._mac = mac.lower()
        self._client = None
        self._char_uuid = None
        self._retry_count = DEFAULT_RETRY_COUNT
        if type == 2:
            self._on_key = ON_KEY2
            self._off_key = OFF_KEY2
        else:
            self._on_key = ON_KEY1
            self._off_key = OFF_KEY1

    async def _connect(self) -> None:
        if self._client is not None:
            return
        try:
            _LOGGER.debug("스위쳐 연결 중")
            self._client = BleakClient(self._mac)
            await self._client.connect()

            services = await self._client.get_services()
            for service in services:
                # print(service)
                # 서비스의 UUID 출력
                #print('\tuuid:', service.uuid)
                if service.uuid == UUID:
                    self._char_uuid = service.characteristics[0].uuid
                #print('\tcharacteristic list:')
                # 서비스의 모든 캐릭터리스틱 출력용
                # for characteristic in service.characteristics:
                    # 캐릭터리스틱 클래스 변수 전체 출력
                #    print('\t\t', characteristic)
                    # UUID
                 #   print('\t\tuuid:', characteristic.uuid)
                    # decription(캐릭터리스틱 설명)
                 #   print('\t\tdescription :', characteristic.description)
                    # 캐릭터리스틱의 속성 출력
                    # 속성 값 : ['write-without-response', 'write', 'read', 'notify']
                 #   print('\t\tproperties :', characteristic.properties)

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
        time.sleep(DEFAULT_RETRY_TIMEOUT)
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


if __name__ == "__main__":
    switcher = IOSwitcher("C8:11:9E:29:CA:57", 1)
    # asyncio.run(switcher.run())
    asyncio.run(switcher.turn_on())
