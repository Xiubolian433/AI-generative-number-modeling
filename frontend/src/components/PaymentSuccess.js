"use client"

import { useEffect, useState } from "react"
import { useSearchParams, useNavigate } from "react-router-dom"
import "./PaymentSuccess.css"
import { API } from "../api"
import { getStoredCredits, setPaidCreditsOnly, setStoredAccessCode } from "../credits"

const PaymentSuccess = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [processing, setProcessing] = useState(true)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const generateDeviceFingerprint = () => {
    const screen = `${window.screen.width}x${window.screen.height}x${window.screen.colorDepth}`
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone
    const platform = navigator.platform
    const language = navigator.language

    return {
      screen_info: screen,
      timezone: timezone,
      platform: platform,
      language: language,
    }
  }

  useEffect(() => {
    const handlePaymentSuccess = async () => {
      try {
        const paymentId = searchParams.get("paymentId")
        const payerId = searchParams.get("PayerID")
        searchParams.get("token")
        searchParams.get("access_code")

        console.log("=== Payment Success Page ===")
        console.log("PaymentId:", paymentId)
        console.log("PayerId:", payerId)

        if (!paymentId || !payerId) {
          throw new Error("Missing payment parameters from PayPal redirect")
        }

        console.log("Waiting for payment processing...")
        await new Promise((resolve) => setTimeout(resolve, 3000))

        const deviceInfo = generateDeviceFingerprint()

        console.log("Executing payment...")
        const response = await API.post("/api/payment/execute", {
          payment_id: paymentId,
          payer_id: payerId,
          ...deviceInfo,
        })

        const data = response.data
        console.log("Execute payment response:", data)

        if (response.status === 200 && data.success) {
          const { paidCredits: currentPaidCredits } = getStoredCredits()
          const newPaidCredits = currentPaidCredits + (data.credits || 0)

          setPaidCreditsOnly(newPaidCredits)
          setStoredAccessCode(data.access_code)

          setResult({
            success: true,
            credits: data.credits,
            accessCode: data.access_code,
            message: data.message,
          })
        } else {
          throw new Error(data.error || `Payment processing failed: ${response.status}`)
        }
      } catch (err) {
        console.error("Payment processing error:", err)
        setError(err.message)
      } finally {
        setProcessing(false)
      }
    }

    handlePaymentSuccess()
  }, [searchParams])

  const handleContinue = () => {
    navigate("/")
  }

  const handleRetryPayment = () => {
    navigate("/")
  }

  const handleCopyAccessCode = () => {
    if (result?.accessCode) {
      navigator.clipboard.writeText(result.accessCode)
      alert("Access code copied to clipboard!")
    }
  }

  if (processing) {
    return (
      <div className="payment-success-container">
        <div className="payment-success-card">
          <div className="spinner"></div>
          <h2>Processing Payment...</h2>
          <p>Please wait while we confirm your payment with PayPal</p>
          <p style={{ fontSize: "0.9rem", color: "#ccc", marginTop: "10px" }}>Activating your credits...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="payment-success-container">
        <div className="payment-success-card error">
          <div className="error-icon">❌</div>
          <h2>Payment Processing Error</h2>
          <p>{error}</p>
          <div className="error-details">
            <p style={{ fontSize: "0.9rem", color: "#ccc", marginBottom: "15px" }}>
              There was an issue processing your payment.
            </p>
            <p style={{ fontSize: "0.9rem", color: "#ccc" }}>
              💡 <strong>What to do:</strong>
              <br />• Make sure you completed the payment on PayPal
              <br />• Check your PayPal account for the transaction
              <br />• If you were charged, contact support with your transaction details
              <br />• Otherwise, you can try the payment again
            </p>
          </div>
          <div style={{ display: "flex", gap: "10px", justifyContent: "center", marginTop: "20px" }}>
            <button onClick={handleRetryPayment} className="continue-btn">
              Try Payment Again
            </button>
            <button onClick={handleContinue} className="continue-btn" style={{ background: "#666" }}>
              Return to Home
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (result?.success) {
    return (
      <div className="payment-success-container">
        <div className="payment-success-card success">
          <div className="success-icon">🎉</div>
          <h2>Payment Successful!</h2>
          <p style={{ color: "#4caf50", fontSize: "1.1rem", marginBottom: "15px" }}>
            Your credits have been instantly activated!
          </p>
          <div className="success-details">
            <div className="detail-item">
              <span className="label">Credits Purchased:</span>
              <span className="value">{result.credits}</span>
            </div>
            <div className="detail-item">
              <span className="label">Status:</span>
              <span className="value" style={{ color: "#4caf50" }}>
                ✅ Active & Ready
              </span>
            </div>
            <div className="detail-item">
              <span className="label">Access Code:</span>
              <span className="value access-code">
                {result.accessCode}
                <button onClick={handleCopyAccessCode} className="copy-btn">
                  📋
                </button>
              </span>
            </div>
          </div>
          <div className="success-message">
            <p>
              🚀 <strong>You can start generating numbers immediately!</strong>
            </p>
            <p>
              💾 <strong>IMPORTANT:</strong> Save your access code now! This is your only way to access credits on other
              devices.
            </p>
            <p>
              ⚠️ <strong>One-time use:</strong> Access codes cannot be recovered if lost. Save it securely!
            </p>
          </div>
          <button onClick={handleContinue} className="continue-btn">
            Start Generating Numbers
          </button>
        </div>
      </div>
    )
  }

  return null
}

export default PaymentSuccess
