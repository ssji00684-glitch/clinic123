from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__)

appointments = {}
token_counter = 1
excel_file = "appointments.xlsx"

if not os.path.exists(excel_file):
    df = pd.DataFrame(columns=["Token", "Name", "Mobile", "Date", "Time"])
    df.to_excel(excel_file, index=False)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    global token_counter
    incoming_msg = request.form.get("Body").strip()
    sender = request.form.get("From")

    resp = MessagingResponse()
    msg = resp.message()

    if sender in appointments and appointments[sender]["status"] == "booked":
        appt = appointments[sender]
        reply = (f"⚠️ आपकी बुकिंग पहले से हो चुकी है!\n"
                 f"👤 नाम: {appt['name']}\n📞 मोबाइल: {appt['mobile']}\n📅 तारीख: {appt['date']}\n"
                 f"🔢 टोकन नंबर: {appt['token']}\n🕘 समय: 9 AM - 2 PM\n\n"
                 f"Your appointment is already booked! If you want to book for another person, please use a new mobile number.")
        msg.body(reply)
        return str(resp)

    if sender not in appointments:
        appointments[sender] = {"step": "name"}
        msg.body("👋 *Welcome to MOMO MAFIYA CLINIC!* 🏥\n\n"
                 "🙏 नमस्ते! *मोमो माफिया क्लिनिक* में आपका स्वागत है।\n\n"
                 "कृपया अपना *पूरा नाम* लिखें / Please type your *Full Name*.")
        return str(resp)

    elif appointments[sender]["step"] == "name":
        appointments[sender]["name"] = incoming_msg
        appointments[sender]["step"] = "mobile"
        msg.body(f"धन्यवाद, *{incoming_msg}*! 😊\nकृपया अपना *मोबाइल नंबर* भेजें / Please share your *Mobile Number.*")
        return str(resp)

    elif appointments[sender]["step"] == "mobile":
        mobile = incoming_msg
        date_today = datetime.now().strftime("%d %b %Y")
        visit_time = "9 AM – 2 PM"

        appointments[sender].update({
            "mobile": mobile,
            "date": date_today,
            "token": token_counter,
            "status": "booked"
        })

        new_entry = pd.DataFrame([{
            "Token": token_counter,
            "Name": appointments[sender]['name'],
            "Mobile": mobile,
            "Date": date_today,
            "Time": visit_time
        }])
        df = pd.read_excel(excel_file)
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_excel(excel_file, index=False)

        msg.body(f"✅ *Appointment booked successfully!* 🎉\n\n"
                 f"🧾 *अपॉइंटमेंट विवरण / Appointment Details:*\n"
                 f"👤 नाम / Name: {appointments[sender]['name']}\n"
                 f"📞 मोबाइल / Mobile: {mobile}\n"
                 f"📅 तारीख / Date: {date_today}\n"
                 f"🔢 टोकन नंबर / Token No: {token_counter}\n"
                 f"🕘 समय / Time: {visit_time}\n\n"
                 f"🙏 धन्यवाद! *मोमो माफिया क्लिनिक* में मिलने के लिए आएं।")

        token_counter += 1
        return str(resp)

    msg.body("❓ Please type 'Hi' to start again / 'नमस्ते' टाइप करें शुरू करने के लिए।")
    return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
