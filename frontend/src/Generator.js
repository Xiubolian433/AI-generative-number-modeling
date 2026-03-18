"use client"

import { useState, useEffect } from "react"
import "./Generator.css"
import { API } from "./api"
import {
  consumeStoredCredit,
  getStoredAccessCode,
  getStoredCredits,
  setServerSyncedCredits,
} from "./credits"

function Generator({ onCreditsUpdate }) {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [displayedResults, setDisplayedResults] = useState([])
  const [displayIndex, setDisplayIndex] = useState(0)
  const [isDisplaying, setIsDisplaying] = useState(false)
  const [remainingCredits, setRemainingCredits] = useState(0)

  const fetchCreditsFromBackend = async () => {
    try {
      const storedAccessCode = getStoredAccessCode()
      if (!storedAccessCode) {
        const { totalCredits } = getStoredCredits()
        setRemainingCredits(totalCredits)
        return totalCredits
      }

      const response = await API.post("/api/credits/verify", {
        access_code: storedAccessCode,
      })

      if (response.data.valid) {
        const totalCredits = response.data.remaining_credits
        setRemainingCredits(totalCredits)
        setServerSyncedCredits(totalCredits)
        return totalCredits
      } else {
        const { totalCredits } = getStoredCredits()
        setRemainingCredits(totalCredits)
        return totalCredits
      }
    } catch (error) {
      console.error("获取积分失败:", error)
      const { totalCredits } = getStoredCredits()
      setRemainingCredits(totalCredits)
      return totalCredits
    }
  }

  const consumeCreditSecurely = async () => {
    try {
      const storedAccessCode = getStoredAccessCode()
      if (!storedAccessCode) {
        setRemainingCredits(consumeStoredCredit())

        if (onCreditsUpdate) onCreditsUpdate()
        return true
      }

      const response = await API.post("/api/credits/consume", {
        access_code: storedAccessCode,
      })

      if (response.data.success) {
        setRemainingCredits(response.data.remaining_credits)
        setServerSyncedCredits(response.data.remaining_credits)

        if (onCreditsUpdate) onCreditsUpdate()
        return true
      } else {
        throw new Error(response.data.message || "积分消费失败")
      }
    } catch (error) {
      console.error("积分消费失败:", error)
      throw error
    }
  }

  const generateNumbers = async () => {
    let currentCredits = remainingCredits
    try {
      currentCredits = await fetchCreditsFromBackend()
    } catch (error) {
      console.error("积分验证失败:", error)
    }

    if (currentCredits <= 0) {
      alert("🎲 Insufficient Credits!\n\nClick the '💳 Top Up' button in the top right to purchase more credits")
      return
    }

    setLoading(true)
    setError(null)
    setResults([])
    setDisplayedResults([])
    setDisplayIndex(0)
    setIsDisplaying(true)

    try {
      await consumeCreditSecurely()

      const response = await API.get("/generate/mega_millions", {
        params: { batch_size: 3 },
      })

      const data = response.data.results
      setResults(data)
    } catch (err) {
      console.error("生成失败:", err)

      if (err.message && err.message.includes("积分")) {
        setError("积分不足，请充值后再试")
        alert("🎲 Insufficient Credits!\n\nClick the '💳 Top Up' button in the top right to purchase more credits")
      } else {
        setError("Failed to fetch numbers. Please try again.")
      }

      setIsDisplaying(false)
      await fetchCreditsFromBackend()
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCreditsFromBackend()

    const interval = setInterval(fetchCreditsFromBackend, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (results.length > 0 && displayIndex < results.length) {
      const timer = setTimeout(() => {
        setDisplayedResults((prev) => [...prev, results[displayIndex]])
        setDisplayIndex((prev) => prev + 1)
      }, 1000)
      return () => clearTimeout(timer)
    } else if (results.length > 0 && displayIndex >= results.length) {
      setIsDisplaying(false)
    }
  }, [results, displayIndex])

  return (
    <div className="generator-container">
      <h1>Play Mega Million</h1>

      <div className="credits-display">
        <span className="credits-text">Total Credits: {remainingCredits}</span>
        {remainingCredits <= 2 && remainingCredits > 0 && <span className="low-credits-warning"> ⚠️ Running Low</span>}
      </div>

      <div className="number-display-wrapper">
        {displayedResults.map((result, index) => (
          <div key={index} className="number-display-row fade-in">
            {result.numbers.map((num, idx) => (
              <div key={idx} className="number filled">
                {num}
              </div>
            ))}
            <div className="mega-ball filled">{result.mega_ball}</div>
          </div>
        ))}
      </div>

      {error && <p className="error">{error}</p>}

      <button
        className={`generate-button ${loading || isDisplaying || remainingCredits <= 0 ? "disabled" : ""}`}
        onClick={generateNumbers}
        disabled={loading || isDisplaying}
      >
        {loading || isDisplaying ? "Generating..." : remainingCredits <= 0 ? "Need Top Up" : "Generate"}
      </button>
    </div>
  )
}

export default Generator
