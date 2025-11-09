# TelegramBot
## [리눅스 기초] 텔레그램 봇 개발
> 텔레그램 봇을 구현한 애플리케이션으로, 텔레그램을 통해 원격으로
> 알림 및 제어를 수행하고 하드웨어(센서/카메라 등)와 연동하는 기능을 포함합니다.

---

## 기능
- 초음파 센서(HC-SR04)로 거리 측정
- USB 카메라로 1.5초 간격 사진 촬영 및 텔레그램 전송
- 거리 기반 LED 깜빡임 속도 조절
- 비동기 기반 멀티태스킹

---

## 하드웨어 구성
- Raspberry Pi 4 Model B
- HC-SR04 (TRIG: GPIO20, ECHO: GPIO16)
- LED 2개 (GPIO6, GPIO5) + 저항 (220Ω)
- USB 카메라 (V4L2 호환)

* 회로도
<img width="862" height="423" alt="스크린샷 2025-11-07 221245" src="https://github.com/user-attachments/assets/54b4467a-3966-499c-a597-446f46a23100" />

---

## 명령어
- `/start` : 사용 가능한 명령어 안내
- `/backward` : 후방 감지(사진 전송 + LED 경고) 시작
- `/stop` : 후방 감지 정지

---

## 사용 방법
1. `TOKEN` 발급 받아 코드에 입력 (`TOKEN`은 절대 공개하지 마세요)
```bash
# 텔레그램 토큰
TOKEN = '토큰 입력'
```
2. 코드 실행
```bash
python3 파일명.py
```
3. 봇에게 `/start` 전송 → 사용 안내 수신
4. `/backward` 전송 → 후방 감지 시작 (사진 전송 및 LED 동작)
5. `/stop` 전송 → 후방 감지 종료
