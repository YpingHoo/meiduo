from celery_tasks.main import app
from utils.ytx_sdk.sendSMS import CCP


@app.task(name="sms_send")
def sms_send(mobile, sms_code, expires, template_id):
    # CCP.sendTemplateSMS(mobile, sms_code, expires, template_id)
    print(sms_code)
