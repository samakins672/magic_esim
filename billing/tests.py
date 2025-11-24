from django.test import TestCase
from unittest.mock import patch, MagicMock
from decimal import Decimal
from billing.utils import initiate_mastercard_checkout, convert_currency, FXConversionError


class MastercardCheckoutCurrencyTests(TestCase):
    """Test that Mastercard Hosted Checkout handles USD, SAR, and other currencies correctly."""

    @patch('billing.utils.requests.post')
    def test_usd_payment_no_conversion(self, mock_post):
        """Test that USD payments are sent directly without conversion to SAR."""
        # Mock successful Mastercard API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "session": {"id": "SESSION123", "version": "abc123"},
            "successIndicator": "SUCCESS_IND",
        }
        mock_post.return_value = mock_response

        result = initiate_mastercard_checkout(
            amount=10.00,
            currency="USD",
            customer_email="test@example.com",
            reference_id="REF123",
            description="Test payment",
        )

        # Verify the result is successful
        self.assertTrue(result["status"])
        self.assertEqual(result["order_currency"], "USD")
        self.assertEqual(result["order_amount"], Decimal("10.00"))

        # Verify the API was called with USD (not SAR)
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        self.assertEqual(payload["order"]["currency"], "USD")
        self.assertEqual(payload["order"]["amount"], "10.00")

    @patch('billing.utils.requests.post')
    def test_sar_payment_no_conversion(self, mock_post):
        """Test that SAR payments are sent directly without conversion."""
        # Mock successful Mastercard API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "session": {"id": "SESSION456", "version": "def456"},
            "successIndicator": "SUCCESS_IND_2",
        }
        mock_post.return_value = mock_response

        result = initiate_mastercard_checkout(
            amount=37.50,
            currency="SAR",
            customer_email="test@example.com",
            reference_id="REF456",
            description="Test SAR payment",
        )

        # Verify the result is successful
        self.assertTrue(result["status"])
        self.assertEqual(result["order_currency"], "SAR")
        self.assertEqual(result["order_amount"], Decimal("37.50"))

        # Verify the API was called with SAR
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        self.assertEqual(payload["order"]["currency"], "SAR")
        self.assertEqual(payload["order"]["amount"], "37.50")

    @patch('billing.utils.convert_currency')
    @patch('billing.utils.requests.post')
    def test_other_currency_converts_to_sar(self, mock_post, mock_convert):
        """Test that non-USD/SAR currencies are converted to SAR."""
        # Mock currency conversion
        mock_convert.return_value = Decimal("38.00")  # Simulated EUR to SAR conversion

        # Mock successful Mastercard API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "session": {"id": "SESSION789", "version": "ghi789"},
            "successIndicator": "SUCCESS_IND_3",
        }
        mock_post.return_value = mock_response

        result = initiate_mastercard_checkout(
            amount=10.00,
            currency="EUR",
            customer_email="test@example.com",
            reference_id="REF789",
            description="Test EUR payment",
        )

        # Verify the result is successful and converted to SAR
        self.assertTrue(result["status"])
        self.assertEqual(result["order_currency"], "SAR")
        self.assertEqual(result["order_amount"], Decimal("38.00"))

        # Verify conversion was called with EUR to SAR
        mock_convert.assert_called_once_with(Decimal("10.00"), "EUR", "SAR")

        # Verify the API was called with SAR
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        self.assertEqual(payload["order"]["currency"], "SAR")
        self.assertEqual(payload["order"]["amount"], "38.00")

    def test_usd_payment_with_lowercase_currency(self):
        """Test that USD in lowercase is properly handled."""
        with patch('billing.utils.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "session": {"id": "SESSION_LC", "version": "lc123"},
                "successIndicator": "SUCCESS_IND_LC",
            }
            mock_post.return_value = mock_response

            result = initiate_mastercard_checkout(
                amount=15.00,
                currency="usd",  # lowercase
                customer_email="test@example.com",
                reference_id="REF_LC",
                description="Test lowercase USD",
            )

            self.assertTrue(result["status"])
            self.assertEqual(result["order_currency"], "USD")
            
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            self.assertEqual(payload["order"]["currency"], "USD")

    def test_default_currency_is_usd(self):
        """Test that when no currency is provided, USD is used as default."""
        with patch('billing.utils.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "session": {"id": "SESSION_DEF", "version": "def123"},
                "successIndicator": "SUCCESS_IND_DEF",
            }
            mock_post.return_value = mock_response

            result = initiate_mastercard_checkout(
                amount=20.00,
                currency=None,  # No currency specified
                customer_email="test@example.com",
                reference_id="REF_DEF",
                description="Test default currency",
            )

            self.assertTrue(result["status"])
            self.assertEqual(result["order_currency"], "USD")
            
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            self.assertEqual(payload["order"]["currency"], "USD")


class CurrencyConversionTests(TestCase):
    """Test the currency conversion utility function."""

    def test_usd_to_sar_conversion(self):
        """Test USD to SAR conversion using the configured rate."""
        result = convert_currency(Decimal("10.00"), "USD", "SAR")
        # Default rate is 3.80
        expected = Decimal("10.00") * Decimal("3.80")
        self.assertEqual(result, expected)

    def test_sar_to_usd_conversion(self):
        """Test SAR to USD conversion."""
        result = convert_currency(Decimal("38.00"), "SAR", "USD")
        # Default rate is 3.80
        expected = Decimal("38.00") / Decimal("3.80")
        self.assertEqual(result, expected)

    def test_same_currency_no_conversion(self):
        """Test that conversion with same source and target returns original amount."""
        result = convert_currency(Decimal("10.00"), "USD", "USD")
        self.assertEqual(result, Decimal("10.00"))

    def test_unsupported_currency_pair_raises_error(self):
        """Test that unsupported currency pairs raise FXConversionError."""
        with self.assertRaises(FXConversionError) as context:
            convert_currency(Decimal("10.00"), "EUR", "GBP")
        self.assertIn("Unsupported currency conversion", str(context.exception))

