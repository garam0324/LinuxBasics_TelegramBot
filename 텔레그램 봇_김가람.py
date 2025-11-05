import cv2
import logging
import os
import asyncio
import RPi.GPIO as GPIO
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 텔레그램 토큰
TOKEN = '토큰 번호'

# 로그 설정
logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)

# 핸들러 함수
# /backward 명령어 입력 시
# /stop 명령어가 입력될 때까지
# 카메라로부터 받은 사진을 실시간으로 텔레그램 채팅창에 전송

# /start 명령어
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("<명령어>\n/backward : 후방 감지 시작\n/stop : 후방 감지 중지")
    
# 핀 설정
LED_PIN_1 = 6
LED_PIN_2 = 5
TRIG = 20
ECHO = 16

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_PIN_1, GPIO.OUT)
GPIO.setup(LED_PIN_2, GPIO.OUT)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# 거리 측정 함수
def measure_distance():
    GPIO.output(TRIG, False)
    time.sleep(0.05)
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    pulse_start = time.time()
    timeout = pulse_start + 0.04

    while GPIO.input(ECHO) == 0 and time.time() < timeout:
        pulse_start = time.time()
        
    pulse_end = time.time()
    
    while GPIO.input(ECHO) == 1 and time.time() < timeout:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    return round(distance, 2)

def get_blink_interval(distance):
    if distance < 10:
        return 0.1
    elif distance > 50:
        return 1.0
    return max(0.1, min(1.0, distance / 50))

# 전역 변수
streaming_task = None
is_streaming = False
led_task = None

# LED 깜빡임 함수
async def blink_led():
    global is_streaming
    while is_streaming:
        dist = measure_distance()
        interval = get_blink_interval(dist)

        # LED1 ON, LED2 OFF
        GPIO.output(LED_PIN_1, GPIO.HIGH)
        GPIO.output(LED_PIN_2, GPIO.LOW)
        await asyncio.sleep(interval)

        # LED1 OFF, LED2 ON
        GPIO.output(LED_PIN_1, GPIO.LOW)
        GPIO.output(LED_PIN_2, GPIO.HIGH)
        await asyncio.sleep(interval)

    # 꺼질 때 둘 다 OFF
    GPIO.output(LED_PIN_1, GPIO.LOW)
    GPIO.output(LED_PIN_2, GPIO.LOW)

# 사진 캡처 함수
async def stream(context, chat_id):
    global is_streaming
    is_streaming = True
    last_warning_time = 0
    
    try:
        # 카메라 열기
        camera = cv2.VideoCapture(0, cv2.CAP_V4L)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not camera.isOpened():
            await context.bot.send_message(chat_id=chat_id, text="카메라를 열 수 없습니다.")
            is_streaming = False
            return

        while is_streaming:
            
            # 거리 측정
            dist = measure_distance()
            
            # 경고 메시지 전송 (5초 간격)
            current_time = time.time()
            if dist < 10 and (current_time - last_warning_time > 5):
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ 너무 가까워요! 물체가 {dist}cm에 있어요!"
                )
                last_warning_time = current_time
            
            # 사진 전송
            ret, frame = camera.read()
            if not ret:
                break
            path = "/tmp/stream.jpg"
            cv2.imwrite(path, frame)
            with open(path, "rb") as photo:
                await context.bot.send_photo(chat_id=chat_id, photo=photo)
            os.remove(path)
            await asyncio.sleep(1.5)
            
    finally:
        camera.release()
        is_streaming = False

# /backward 명령어 → 영상 스트리밍 시작 (단, 텔레그램은 실시간 영상 서비스를 지원하지 않으므로 1.5초 간격으로 사진 전송)
async def backward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global streaming_task, led_task
    if streaming_task is not None and not streaming_task.done():
        await update.message.reply_text("이미 작동 중입니다.")
        return

    await update.message.reply_text("후방 감지를 시작합니다. /stop 으로 종료하세요.")
    print("후방 감지 시작")
    chat_id = update.effective_chat.id
    is_streaming = True
    
    # 스트리밍과 LED 깜빡임 동시에
    streaming_task = asyncio.create_task(stream(context, chat_id))
    led_task = asyncio.create_task(blink_led())

# /stop 명령어 → 영상 전송 종료
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_streaming, streaming_task, led_task
    if not is_streaming:
        await update.message.reply_text("후방 감지 실행 중이 아닙니다.")
        return

    is_streaming = False
    await update.message.reply_text("후방 감지를 중단했습니다.")
    print("텔레그램 봇 작동 중지")
    print("후방 감지 중지")
    
    # stop 후 예외처리
    try:
        if streaming_task:
            streaming_task.cancel()
            await streaming_task
    except asyncio.CancelledError:
        pass
    
    try:
        if led_task:
            led_task.cancel()
            await led_task
    except asyncio.CancelledError:
        pass

    streaming_task = None
    led_task = None
    
# main 함수
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("backward", backward))
    app.add_handler(CommandHandler("stop", stop))

    try:
        app.run_polling()
        print("텔레그램 봇 작동 중...")

    finally:
        GPIO.cleanup()  # 여기서 한 번만 cleanup

if __name__ == '__main__':

    main()
