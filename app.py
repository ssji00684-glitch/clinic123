from flask import Flask, request, jsonify
import requests, os
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd

load_dotenv()
app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

appointments = {}
token_counter = 1
excel_file = "appointments.xlsx"

if not os.path.exists(excel_file):
    df = pd.DataFrame(columns=["Token", "Name", "Mobile", "Date", "Time"])
    df.to_excel(excel_file, index=False)

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Invalid verification", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    global token_counter
    data = request.get_json()
    if data and data.get("entry"):
        try:
            msg = data['entry'][0]['changes'][0]['value']['messages'][0]
            user_id = msg['from']
            user_text = msg['text']['body'].strip()

            if user_id in appointments and appointments[user_id]["status"] == "booked":
                appt = appointments[user_id]
                send_message(
                    user_id,
                    f"⚠️ *Your appointment is already booked!* \n\n"
                    f"👤 Name / नाम: {appt['name']}\n"
                    f"📞 Mobile / मोबाइल: {appt['mobile']}\n"
                    f"📅 Date / तारीख: {appt['date']}\n"
                    f"🔢 Token No / टोकन नंबर: {appt['token']}\n"
                    f"🕘 Visit Time / समय: 9 AM – 2 PM\n\n"
                    f"If you want to book for someone else, please use a *different mobile number.*\n"
                    f"यदि आप किसी और के लिए बुक करना चाहते हैं, तो कृपया *अलग मोबाइल नंबर* का उपयोग करें।"
                )
                return jsonify({"status": "received"}), 200

            if user_id not in appointments:
                appointments[user_id] = {"step": "name"}
                send_message(
                    user_id,
                    "👋 *Welcome to MOMO MAFIYA CLINIC!* 🏥\n\n"
                    "🙏 नमस्ते! *मोमो माफिया क्लिनिक* में आपका स्वागत है।\n\n"
                    "कृपया अपना *पूरा नाम* लिखें / Please type your *Full Name*."
                )
                return jsonify({"status": "received"}), 200

            elif appointments[user_id]["step"] == "name":
                appointments[user_id]["name"] = user_text
                appointments[user_id]["step"] = "mobile"
                send_message(
                    user_id,
                    f"धन्यवाद, *{user_text}*! 😊\nकृपया अपना *मोबाइल नंबर* भेजें / Please share your *Mobile Number.*"
                )
                return jsonify({"status": "received"}), 200

            elif appointments[user_id]["step"] == "mobile":
                mobile = user_text
                date_today = datetime.now().strftime("%d %b %Y")
                visit_time = "9 AM – 2 PM"

                appointments[user_id].update({
                    "mobile": mobile,
                    "date": date_today,
                    "token": token_counter,
                    "status": "booked"
                })

                new_row = pd.DataFrame([{
                    "Token": token_counter,
                    "Name": appointments[user_id]['name'],
                    "Mobile": mobile,
                    "Date": date_today,
                    "Time": visit_time
                }])
                df = pd.read_excel(excel_file)
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_excel(excel_file, index=False)

                send_message(
                    user_id,
                    f"✅ *Appointment booked successfully!* 🎉\n\n"
                    f"🧾 *अपॉइंटमेंट विवरण / Appointment Details:*\n"
                    f"👤 नाम / Name: {appointments[user_id]['name']}\n"
                    f"📞 मोबाइल / Mobile: {mobile}\n"
                    f"📅 तारीख / Date: {date_today}\n"
                    f"🔢 टोकन नंबर / Token No: {token_counter}\n"
                    f"🕘 समय / Time: {visit_time}\n\n"
                    f"🙏 धन्यवाद! *मोमो माफिया क्लिनिक* में मिलने के लिए आएं।"
                )
                token_counter += 1
                return jsonify({"status": "received"}), 200

        except Exception as e:
            print("Error:", e)
    return jsonify({"status": "received"}), 200

def send_message(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to, "text": {"body": text}}
    requests.post(url, headers=headers, json=data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
