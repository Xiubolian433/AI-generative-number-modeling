"use client"

import { useNavigate } from "react-router-dom"
import "./PaymentSuccess.css"

const PaymentCancel = () => {
  const navigate = useNavigate()

  const handleReturnHome = () => {
    navigate("/")
  }

  const handleRetryPayment = () => {
    navigate("/")
  }

  return (
    <div className="payment-success-container">
      <div className="payment-success-card error">
        <div className="error-icon">❌</div>
        <h2>Payment Cancelled</h2>
        <p>Your payment was cancelled and no charges were made.</p>

        <div className="error-details">
          <p style={{ fontSize: "0.9rem", color: "#ccc", marginBottom: "15px" }}>
            You can try the payment process again or return to the main page.
          </p>
          <p style={{ fontSize: "0.9rem", color: "#ccc" }}>
            💡 <strong>Need help?</strong>
            <br />• Make sure you have sufficient funds in your PayPal account
            <br />• Check your internet connection
            <br />• Try using a different payment method
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", justifyContent: "center", marginTop: "20px" }}>
          <button onClick={handleRetryPayment} className="continue-btn">
            Try Payment Again
          </button>
          <button onClick={handleReturnHome} className="continue-btn" style={{ background: "#666" }}>
            Return to Home
          </button>
        </div>
      </div>
    </div>
  )
}

export default PaymentCancel
