import sys
import bluepy
import time
import binascii
import logging

DEFAULT_RETRY_COUNT = 5
DEFAULT_RETRY_TIMEOUT = 1

ON_KEY1 = binascii.a2b_hex("00")
OFF_KEY1 = binascii.a2b_hex("01")

ON_KEY2 = binascii.a2b_hex("05")
OFF_KEY2 = binascii.a2b_hex("03")
#1구의 경우 00,01
#2구의 경우 05,03

UUID = "0000150b-0000-1000-8000-00805f9b34fb"


_LOGGER = logging.getLogger(__name__)

class IOSwitcher:
    def __init__(self, mac, type=1, **kwargs) -> None:
        """IO 스위쳐 초기화."""
        self._mac = mac.replace("-", ":").lower()
        self._device = None
        self._retry_count = DEFAULT_RETRY_COUNT
        if type == 2:
            self._on_key = ON_KEY2
            self._off_key = OFF_KEY2
        else :
            self._on_key = ON_KEY1
            self._off_key = OFF_KEY1

    def _connect(self) -> None:
        if self._device is not None:
            return
        try:
            _LOGGER.debug("스위쳐 연결 중")
            self._device = bluepy.btle.Peripheral(
                self._mac, bluepy.btle.ADDR_TYPE_RANDOM
            )
            _LOGGER.debug("스위쳐 연결 완료!")
        except bluepy.btle.BTLEException:
            _LOGGER.debug("스위쳐 연결 실패", exc_info=True)
            self._device = None
            raise

    def _disconnect(self) -> None:
        if self._device is None:
            return
        _LOGGER.debug("연결 끊기 완료")
        try:
            self._device.disconnect()
        except bluepy.btle.BTLEException:
            _LOGGER.warning("연결을 끊는중 에러 발생", exc_info=True)
        finally:
            self._device = None

    def turn_on(self) -> bool:
        """불을 켭니다."""
        return self._sendcommand(self._on_key, self._retry_count)
    def turn_off(self) -> bool:
        """불을 끕니다."""
        return self._sendcommand(self._off_key, self._retry_count)
    def _commandkey(self, key) -> str:
        #여기다 타입별로 명령어 추가
        return key
    def _sendcommand(self, key, retry) -> bool:
        send_success = False
        command = self._commandkey(key)
        try:
            self._connect()
            send_success = self._writekey(command)
        except bluepy.btle.BTLEException:
            _LOGGER.warning("블루투스 통신중 오류가 발생했습니다.", exc_info=True)
        finally:
            self._disconnect()
        if send_success:
            return True
        if retry < 1:
            _LOGGER.error(
                "스위쳐 통신 실패..", exc_info=True
            )
            return False
        _LOGGER.warning("스위쳐 연결 실패. 다시 시도 남은 횟수 %d", retry)
        time.sleep(DEFAULT_RETRY_TIMEOUT)
        return self._sendcommand(key, retry - 1)
    def _writekey(self, key) -> bool:
        _LOGGER.debug("데이터 통신 준비")
        handle_service = self._device.getServiceByUUID(UUID)
        handle = handle_service.getCharacteristics()[0]
        _LOGGER.debug("키 보내는중, %s", key)
        write_result = handle.write(key)
        print(write_result)
        if not write_result:
            _LOGGER.error(
                "명령어를 보냈으나 결과값이 돌아오지않았습니다. 아이오 스위쳐를 확인해보세요."
            )
        else:
            _LOGGER.info("스위쳐로 데이터를 보냈습니다. (MAC: %s)", self._mac)
        return write_result
        