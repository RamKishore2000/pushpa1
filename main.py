import razorpay  # Razorpay client library
import webview  # Use pywebview for webview handling
from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.dialog import MDDialog

# Razorpay API credentials (Test Mode)
RAZORPAY_KEY_ID = 'rzp_test_hf2afT5lk394ug'
RAZORPAY_KEY_SECRET = 'bSTTNZLyxYZXdNzb2aRUHLvT'

# Initialize Razorpay client
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

kv = """
BoxLayout:
    orientation: 'vertical'
    padding: 20
    spacing: 20

    ScrollView:
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height

            MDLabel:
                id: wallet_label
                text: f"Wallet Balance: ₹{app.wallet_balance:.2f}"
                theme_text_color: "Primary"
                size_hint_y: None
                height: self.texture_size[1]

            MDTextField:
                id: amount_input
                hint_text: "Enter Amount"
                mode: "rectangle"
                size_hint_y: None
                height: "40dp"

            MDRaisedButton:
                text: "Pay Now"
                size_hint_y: None
                height: "50dp"
                on_release: app.pay_now(self)
"""

class Kishore(MDApp):
    wallet_balance = 0  # Global wallet balance for the app

    def build(self):
        return Builder.load_string(kv)

    def create_razorpay_order(self, amount_in_paise):
        """
        Function to create Razorpay order.
        :param amount_in_paise: The amount to be captured by Razorpay in paise
        """
        try:
            order_data = client.order.create({
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": "receipt#1",
                "payment_capture": 1
            })
            if order_data.get("id"):
                print(f"Razorpay Order Created Successfully: {order_data['id']}")
                return order_data
            else:
                print("Error: Order data does not contain an ID")
                return None
        except Exception as e:
            print(f"Error creating Razorpay order: {str(e)}")
            return None

    def pay_now(self, instance):
        """
        Function to handle the payment process when 'Pay Now' is clicked.
        It creates an order on Razorpay and opens Razorpay checkout in a pywebview.
        """
        # Get the entered amount from the MDTextInput field
        amount_input = self.root.ids.amount_input.text

        if not amount_input:
            # Show an alert dialog if no amount is entered
            dialog = MDDialog(
                title="Error",
                text="Please enter a valid amount",
                size_hint=(0.7, 1)
            )
            dialog.open()
            return

        try:
            # Convert the amount to paise (1 INR = 100 paise)
            amount_in_paise = int(amount_input) * 100
        except ValueError:
            # Show an error dialog if the amount is invalid
            dialog = MDDialog(
                title="Invalid Amount",
                text="Please enter a valid number",
                size_hint=(0.7, 1)
            )
            dialog.open()
            return

        # Create order and get order details from Razorpay API
        order_data = self.create_razorpay_order(amount_in_paise)
        if order_data:
            order_id = order_data['id']
            amount = order_data['amount']
            currency = order_data['currency']

            # Create Razorpay checkout options in HTML/JavaScript
            checkout_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
            </head>
            <body>
                <script>
                    var options = {{
                        key: '{RAZORPAY_KEY_ID}',  // Razorpay API Key
                        amount: {amount},  // Amount in paise (integer)
                        currency: '{currency}',
                        name: 'Your Company',
                        description: 'Test Payment',
                        order_id: '{order_id}',  // Order ID from Razorpay API
                        handler: function(response) {{
                            // Call payment success handler to update wallet
                            window.pywebview.api.payment_success(response.razorpay_payment_id, {amount});
                            
                            // Close the Razorpay payment modal after success
                            window.pywebview.api.close_payment_modal();  // This closes the webview window automatically after the payment is successful
                        }},
                        modal_error: function(response) {{
                            alert('Payment failed: ' + response.error.description);
                        }},
                        prefill: {{
                            name: 'John Doe',
                            email: 'john.doe@example.com',
                            contact: '8639028233',
                        }},
                        theme: {{
                            color: '#F37254'
                        }}
                    }};
                    var rzp1 = new Razorpay(options);
                    rzp1.open();
                </script>
            </body>
            </html>
            """

            # Directly open the Razorpay checkout HTML in the webview
            self.open_payment_modal(checkout_html)

    def open_payment_modal(self, html_content):
        """
        Function to open Razorpay payment modal directly from the HTML content string.
        :param html_content: The HTML content that includes the Razorpay checkout script
        """
        try:
            # Open Razorpay checkout using pywebview directly from the HTML string
            webview.create_window("Razorpay Payment", html=html_content, js_api=self)
            webview.start()
        except Exception as e:
            print(f"Error opening Razorpay payment modal: {e}")

    def payment_success(self, payment_id, amount):
        """
        Simulate payment success and update wallet balance.
        :param payment_id: Payment ID received after a successful transaction
        :param amount: Amount credited to the wallet
        """
        self.update_wallet(amount)
        
        self.close_payment_modal()  # Close the Razorpay modal after success

    def close_payment_modal(self):
        """
        Function to close the Razorpay payment modal window.
        This will be called after a successful payment.
        """
        try:
            webview.destroy()  # Close the window using the destroy method
        except Exception as e:
            print(f"Error closing the window: {e}")

    def update_wallet(self, amount_in_paise):
        """
        Function to update the wallet balance when a successful payment is made.
        :param amount_in_paise: The amount to be credited to the wallet
        """
        self.wallet_balance += amount_in_paise / 100  # Convert paise to INR
        # Update the wallet balance label in the KV file dynamically
        self.root.ids.wallet_label.text = f"Wallet Balance: ₹{self.wallet_balance:.2f}"


if __name__ == "__main__":
    Kishore().run()
