# PySwitcherIO(파이썬 스위쳐 아이오) 

## 스위처(https://try.i-o.studio/#/) 제품을 파이썬으로 컨트롤 하는 코드입니다.

누군가 만들기를 기다렸는데... 결국 참다 못해 만든 파이썬 라이브러리.

## Example

```python
#1구의 경우
import pyswitcherio
io = pyswitcherio.IOSwitcher("XX:XX:XX:XX:XX:XX", 1)
io.turn_on()
io.turn_off()
#2구의 경우
import pyswitcherio
io = pyswitcherio.IOSwitcher("XX:XX:XX:XX:XX:XX", 2)
io.turn_on()
io.turn_off()
```

## Installation

pip install PySwitcherIO==0.0.1

## License

MIT