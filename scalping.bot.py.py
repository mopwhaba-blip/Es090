
# ----------------------------------------------------
# 2. كود البوت الخاص بك يبدأ من هنا (مثال توضيحي)#
# ----------------------------------------------------
import requests
import pandas as pd
import pandas_ta as ta

print("\n[✓] جميع المكتبات جاهزة! البوت يعمل الآن على بايثون 3.11...")

# أضف بقية منطق التداول الخاص بالبوت هنا (لوج جلب البيانات، التحليل، إلخ)


import time
import json
import requests
import pandas as pd
import pandas_ta as ta

# --- [بيانات حسابك في EXNESS] ---
ACCOUNT_ID = "262983331"
PASSWORD = "Estfan&&mop099"
SERVER = "Exness-MT5Trial16"
SYMBOL = "XAUUSD"  # الذهب
LOT_SIZE = 0.01

# إعدادات الهدف ووقف الخسارة بالنقاط (Points)
TAKE_PROFIT_POINTS = 300 
STOP_LOSS_POINTS = 200

# عنوان خادم الويب البديل للربط مع ميتاتريدر (Web Terminal Bridge)
# ملاحظة: نستخدم منفذ الاتصال المباشر لبروكر إكسنس
WEB_API_URL = f"https://webterminal.exness.com/api" 

def login_to_web_terminal():
    """تسجيل الدخول لجلب رمز الجلسة (Session Token) من خادم إكسنس مباشرة"""
    payload = {
        "login": ACCOUNT_ID,
        "password": PASSWORD,
        "server": SERVER,
        "platform": "mt5"
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(f"{WEB_API_URL}/auth", json=payload, headers=headers)
        if response.status_code == 200:
            token = response.json().get("token")
            print(f"تم الاتصال بنجاح عبر الويب! رمز الجلسة: {token[:10]}...")
            return token
        else:
            print(f"فشل الاتصال بالويب تيرمينال: {response.text}")
            return None
    except Exception as e:
        print(f"خطأ أثناء محاولة تسجيل الدخول السحابي: {e}")
        return None

def get_rates_via_web(symbol, count=100):
    """جلب أسعار السوق الحالية عبر الويب لبناء المؤشرات"""
    # نطلب الأسعار اللحظية لشمعة الدقيقة (M1) لشارت الذهب
    url = f"{WEB_API_URL}/history?symbol={symbol}&resolution=1&count={count}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['candles']) # تحويل البيانات لجدول
            df['close'] = df['c'].astype(float) # سعر الإغلاق
            
            # حساب المؤشرات الفنية (RSI, Bollinger Bands, EMA)
            df['EMA_20'] = ta.ema(df['close'], length=20)
            bbands = ta.bbands(df['close'], length=20, std=2)
            df['BB_upper'] = bbands['BBU_20_2.0']
            df['BB_lower'] = bbands['BBL_20_2.0']
            df['RSI'] = ta.rsi(df['close'], length=14)
            return df
    except Exception as e:
        print(f"خطأ أثناء جلب أسعار الشارت: {e}")
    return None

def send_web_order(token, action, symbol, lot, sl_points, tp_points):
    """إرسال أمر فتح صفقة مباشرة إلى سيرفر Exness عبر الويب تيرمينال"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # تحديد الاتجاه (شراء 0، بيع 1 في نظام MT5 Web)
    trade_type = 0 if action == "BUY" else 1
    
    payload = {
        "symbol": symbol,
        "volume": lot,
        "operation": trade_type,
        "sl_points": sl_points,
        "tp_points": tp_points,
        "deviation": 10
    }
    
    try:
        response = requests.post(f"{WEB_API_URL}/trade", json=payload, headers=headers)
        if response.status_code == 200:
            print(f"🚀 تم تنفيذ صفقة {action} للذهب لوت {lot} عبر الهاتف بنجاح!")
        else:
            print(f"فشل تنفيذ الصفقة عبر السيرفر: {response.text}")
    except Exception as e:
        print(f"خطأ أثناء إرسال أمر التداول: {e}")

def main():
    token = login_to_web_terminal()
    if not token:
        return

    print("بدء المراقبة والتحليل للاسكالبينج على الهاتف (Termux)...")
    
    while True:
        try:
            df = get_rates_via_web(SYMBOL)
            if df is not None:
                last_row = df.iloc[-1]
                close_price = last_row['close']
                ema = last_row['EMA_20']
                bb_upper = last_row['BB_upper']
                bb_lower = last_row['BB_lower']
                rsi = last_row['RSI']
                
                # --- [شروط الاستراتيجية] ---
                # شراء: السعر فوق EMA، ويلمس بولنجر السفلي، وRSI أقل من 35 (تشبع بيعي)
                if (close_price > ema) and (close_price <= bb_lower) and (rsi < 35):
                    print(f"إشارة شراء مفعّلة! السعر الحالي: {close_price}")
                    send_web_order(token, "BUY", SYMBOL, LOT_SIZE, STOP_LOSS_POINTS, TAKE_PROFIT_POINTS)
                    time.sleep(60) # تجميد مؤقت لمنع تكرار الصفقات في نفس الشمعة
                
                # بيع: السعر تحت EMA، ويلمس بولنجر العلوي، وRSI أكبر من 65 (تشبع شرائي)
                elif (close_price < ema) and (close_price >= bb_upper) and (rsi > 65):
                    print(f"إشارة بيع مفعّلة! السعر الحالي: {close_price}")
                    send_web_order(token, "SELL", SYMBOL, LOT_SIZE, STOP_LOSS_POINTS, TAKE_PROFIT_POINTS)
                    time.sleep(60)
            
            # فحص السوق كل 15 ثانية
            time.sleep(15)
            
        except KeyboardInterrupt:
            print("تم إيقاف البوت يدوياً.")
            break
        except Exception as e:
            print(f"حدث خطأ في الاتصال: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()