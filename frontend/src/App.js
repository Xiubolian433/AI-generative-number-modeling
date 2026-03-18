"use client"

import { useState, useEffect } from "react"
import "./App.css"
import Generator from "./Generator"
import "./Generator.css"

import PowerBallGenerator from "./powerball_generator"
import "./powerball_generator.css"

import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom"
import HistoryNumbers from "./components/HistoryNumbers"
import HistoryStatistic from "./components/HistoryStatistic"
import TypewriterIntro from "./components/TypewriterIntro"
import PaymentSuccess from "./components/PaymentSuccess"
import PaymentCancel from "./components/PaymentCancel"
import { API_BASE_URL } from "./api"
import {
  getStoredCredits,
  getStoredAccessCode,
  initializeCreditsIfNeeded,
  setServerSyncedCredits,
  setStoredAccessCode,
  subscribeToCreditsUpdated,
} from "./credits"

function App() {
  const [visitCount, setVisitCount] = useState(0)
  const [showPaymentModal, setShowPaymentModal] = useState(false)
  const [totalCredits, setTotalCredits] = useState(0)

  const updateTotalCredits = () => {
    setTotalCredits(getStoredCredits().totalCredits)
  }

  useEffect(() => {
    const currentCount = localStorage.getItem("visitCount") || 0
    const newCount = Number.parseInt(currentCount) + 1

    localStorage.setItem("visitCount", newCount)
    setVisitCount(newCount)

    initializeCreditsIfNeeded()
    updateTotalCredits()

    const syncCreditsFromBackend = async () => {
      const accessCode = getStoredAccessCode()
      if (!accessCode) {
        updateTotalCredits()
        return
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/credits/verify`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            access_code: accessCode,
          }),
        })

        const data = await response.json()
        if (response.ok && data.valid) {
          setServerSyncedCredits(data.remaining_credits)
        }
      } catch (error) {
        console.error("Failed to sync credits from backend:", error)
      }
    }

    syncCreditsFromBackend()

    return subscribeToCreditsUpdated(() => updateTotalCredits())
  }, [])

  const handleTopUpClick = () => {
    setShowPaymentModal(true)
  }

  const closePaymentModal = () => {
    setShowPaymentModal(false)
  }

  const [currentGenerator, setCurrentGenerator] = useState(null)

  const handleMegaMillionClick = () => {
    setCurrentGenerator("MegaMillion")
  }

  const handlePowerBallClick = () => {
    setCurrentGenerator("PowerBall")
  }

  const handleBackClick = () => {
    setCurrentGenerator(null)
  }

  return (
    <Router>
      <div className="App">
        <div id="tsparticles"></div>
        <div className="animated-background"></div>
        <div className="navbar">
          <h1>Welcome to Lottery AI Generator</h1>
          <nav>
            <Link to="/history-statistic">History Statistic</Link>
            <Link to="/history-numbers">History Numbers</Link>
            <button className="topup-button" onClick={handleTopUpClick}>
              💳 Top Up ({totalCredits})
            </button>
          </nav>
        </div>
        <Routes>
          <Route
            path="/"
            element={
              <>
                {currentGenerator === null && <TypewriterIntro />}
                {currentGenerator === null ? (
                  <div className="button-container">
                    <button className="Mega-Million" onClick={handleMegaMillionClick}>
                      Mega Million
                    </button>
                    <button className="Power-Ball" onClick={handlePowerBallClick}>
                      Power Ball
                    </button>
                  </div>
                ) : currentGenerator === "MegaMillion" ? (
                  <div className="generator-wrapper">
                    <Generator onCreditsUpdate={updateTotalCredits} />
                    <button className="back-button" onClick={handleBackClick}>
                      Back
                    </button>
                  </div>
                ) : (
                  <div className="generator-wrapper">
                    <PowerBallGenerator onCreditsUpdate={updateTotalCredits} />
                    <button className="back-button" onClick={handleBackClick}>
                      Back
                    </button>
                  </div>
                )}
              </>
            }
          />
          <Route path="/history-statistic" element={<HistoryStatistic />} />
          <Route path="/history-numbers" element={<HistoryNumbers />} />
          <Route path="/payment/success" element={<PaymentSuccess />} />
          <Route path="/payment/cancel" element={<PaymentCancel />} />
        </Routes>
        <div className="visit-counter">
          <span>Total Visits: {visitCount.toLocaleString()}</span>
        </div>

        {showPaymentModal && <PaymentModal onClose={closePaymentModal} onSuccess={updateTotalCredits} />}
      </div>
    </Router>
  )
}

function PaymentModal({ onClose, onSuccess }) {
  const [accessCode, setAccessCode] = useState("")
  const [showCodeInput, setShowCodeInput] = useState(false)
  const [processing, setProcessing] = useState(false)

  const paymentOptions = [
    { price: 1, credits: 5, popular: false },
    { price: 5, credits: 30, popular: true },
    { price: 10, credits: 70, popular: false },
    { price: 20, credits: 150, popular: false },
  ]

  const handlePackageSelect = async (option) => {
    setProcessing(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/payment/create-order`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          package_price: option.price,
        }),
      })

      const data = await response.json()

      if (response.ok && data.approval_url) {
        window.location.href = data.approval_url
      } else {
        throw new Error(data.message || data.error || "Failed to create payment order")
      }
    } catch (error) {
      console.error("Payment creation failed:", error)
      alert(error.message || "Payment creation failed. Please try again.")
      setProcessing(false)
    }
  }

  const handleRestoreCode = async () => {
    if (accessCode.trim()) {
      try {
        const response = await fetch(`${API_BASE_URL}/api/credits/verify`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            access_code: accessCode,
          }),
        })

        const data = await response.json()

        if (data.valid) {
          setServerSyncedCredits(data.remaining_credits)
          setStoredAccessCode(accessCode)

          alert(`✅ Successfully restored ${data.remaining_credits} generation credits!`)
          onSuccess()
          onClose()
        } else {
          alert("❌ Invalid access code")
        }
      } catch (error) {
        console.error("Access code verification failed:", error)
        alert("❌ Verification failed. Please try again.")
      }
    }
  }

  return (
    <div className="payment-modal-overlay">
      <div className="payment-modal">
        <div className="modal-header">
          <h3>🎲 Choose Your Package</h3>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        {processing && (
          <div className="processing-section">
            <div className="spinner"></div>
            <h4>Processing Payment...</h4>
            <p>Please wait while we process your payment</p>
          </div>
        )}

        {!processing && !showCodeInput && (
          <>
            <div className="payment-options">
              {paymentOptions.map((option, index) => (
                <div
                  key={index}
                  className={`payment-option ${option.popular ? "popular" : ""}`}
                  onClick={() => handlePackageSelect(option)}
                >
                  {option.popular && <div className="popular-badge">🔥 Popular</div>}
                  <div className="price">${option.price}</div>
                  <div className="credits">{option.credits} Credits</div>
                  <div className="per-credit">${(option.price / option.credits).toFixed(2)}/credit</div>
                </div>
              ))}
            </div>

            <div className="modal-footer">
              <p className="no-account-note">✅ No Registration ✅ Instant Use ✅ Cross-Device Access Code</p>
              <button className="code-restore-btn" onClick={() => setShowCodeInput(true)}>
                🔑 I Have Access Code
              </button>
            </div>
          </>
        )}

        {!processing && showCodeInput && (
          <div className="code-input-section">
            <h4>🔑 Enter Access Code</h4>
            <p>Purchased on another device? Enter your access code to restore credits</p>
            <input
              type="text"
              placeholder="Enter access code (e.g., LC-A1B2C3)"
              value={accessCode}
              onChange={(e) => setAccessCode(e.target.value.toUpperCase())}
              className="code-input"
            />
            <div className="code-actions">
              <button onClick={handleRestoreCode} className="restore-btn">
                Restore Credits
              </button>
              <button onClick={() => setShowCodeInput(false)} className="back-btn">
                Back to Purchase
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
