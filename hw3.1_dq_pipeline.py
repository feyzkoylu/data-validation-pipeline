import great_expectations as ge
import pandas as pd
import sys
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Slack Webhook URL
SLACK_WEBHOOK_URL = "YOUR_SLACK_WEBHOOK_URL"
slack_client = WebClient(token="YOUR_SLACK_TOKEN")

# Veri kümesini yükle
df = pd.read_csv('data/amazon_orders.csv')

# Great Expectations bağlamı oluştur
context = ge.data_context.DataContext()

# Veri kümesi için Expectation Suite oluştur
suite = context.create_expectation_suite('amazon_order_suite', overwrite_existing=True)

# Beklentiler ekle
df_ge = ge.from_pandas(df)
df_ge.expect_column_values_to_not_be_null('order_id')
df_ge.expect_column_values_to_be_in_set('currency', ['INR'])
df_ge.expect_column_values_to_be_in_set('ship_country', ['IN'])
df_ge.expect_column_values_to_be_in_set('status', ['Pending', 'Shipped', 'Delivered', 'Canceled'])

# Doğrulama yap
validation_results = df_ge.validate(expectation_suite_name="amazon_order_suite")

# Doğrulama sonuçlarını yazdır
print(validation_results)

# Slack'e bildirim gönder
def send_slack_notification(validation_results):
    failed_expectations = [result for result in validation_results["results"] if not result["success"]]
    if failed_expectations:
        failed_expectations_summary = "\n".join(
            [f"- {result['expectation_config']['expectation_type']}: {result['expectation_config']['kwargs']}" 
             for result in failed_expectations]
        )

        message = f"Data validation failed with the following issues:\n{failed_expectations_summary}"

        try:
            response = slack_client.chat_postMessage(
                channel='#your-channel',  # Slack kanalını buraya yaz
                text=message
            )
            print(f"Message sent to Slack channel: {response['channel']}")
        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")

# Eğer doğrulama başarısızsa Slack bildirimi gönder
if validation_results["success"] is False:
    send_slack_notification(validation_results)
    sys.exit(1)  # CI sürecinde hata verir

sys.exit(0)  # Başarı durumunda çıkış yap
