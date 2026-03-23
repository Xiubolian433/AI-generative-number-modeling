"use client"

import { useState, useEffect } from "react"
import "./HistoryNumbers.css"
import { useNavigate } from "react-router-dom"
import { API } from "../api.js"

const HISTORY_NUMBERS_CACHE_KEY = "historyNumbersCache"

const HistoryNumbers = () => {
  const [data, setData] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [lotteryType, setLotteryType] = useState("MegaMillion")
  const [error, setError] = useState(null)
  const [isInitialLoad, setIsInitialLoad] = useState(true)

  const itemsPerPage = 20
  const maxPageButtons = 10

  const tableConfig = {
    MegaMillion: {
      headers: ["Date", "Number1", "Number2", "Number3", "Number4", "Number5", "Mega Ball", "Megaplier", "Jackpot"],
      fields: [
        "DrawingDate",
        "Number1",
        "Number2",
        "Number3",
        "Number4",
        "Number5",
        "MegaBall",
        "Megaplier",
        "JackPot",
      ],
    },
    PowerBall: {
      headers: [
        "Date",
        "Number1",
        "Number2",
        "Number3",
        "Number4",
        "Number5",
        "Power Ball",
        "Jackpot",
        "Estimated Cash Value",
      ],
      fields: [
        "DrawingDate",
        "Number1",
        "Number2",
        "Number3",
        "Number4",
        "Number5",
        "PowerBall",
        "Jackpot",
        "EstimatedCashValue",
      ],
    },
  }

  const navigate = useNavigate()

  const readCache = () => {
    try {
      return JSON.parse(window.sessionStorage.getItem(HISTORY_NUMBERS_CACHE_KEY) || "{}")
    } catch (cacheError) {
      console.warn("Failed to read history numbers cache:", cacheError)
      return {}
    }
  }

  const writeCache = (type, nextData) => {
    try {
      const currentCache = readCache()
      window.sessionStorage.setItem(
        HISTORY_NUMBERS_CACHE_KEY,
        JSON.stringify({
          ...currentCache,
          [type]: nextData,
        }),
      )
    } catch (cacheError) {
      console.warn("Failed to write history numbers cache:", cacheError)
    }
  }

  const handleBackToHome = () => {
    navigate("/")
  }

  useEffect(() => {
    let ignore = false

    const fetchData = async (type, options = {}) => {
      const { background = false } = options
      let lastError = null

      const cachedData = readCache()[type]
      const hasCachedData = Array.isArray(cachedData) && cachedData.length > 0

      if (!background) {
        setLoading(true)
        setError(null)
        if (hasCachedData) {
          setData(cachedData)
          setIsInitialLoad(false)
        }
      }

      try {
        for (let attempt = 1; attempt <= 2; attempt += 1) {
          try {
            const response = await API.get(`/api/history-numbers/${type}`)
            const nextData = Array.isArray(response.data) ? response.data : []

            writeCache(type, nextData)

            if (!background && !ignore) {
              setData(nextData)
              setIsInitialLoad(false)
            }
            return
          } catch (requestError) {
            lastError = requestError
            if (attempt < 2) {
              await new Promise((resolve) => setTimeout(resolve, 1500))
            }
          }
        }

        throw lastError || new Error("History numbers request failed")
      } catch (error) {
        console.error("Error fetching data:", error)
        if (!background && !ignore) {
          if (!hasCachedData) {
            setData([])
          }
          setError(hasCachedData ? null : "Failed to fetch data. Please try again later.")
        }
      } finally {
        if (!background && !ignore) {
          setLoading(false)
        }
      }
    }

    fetchData(lotteryType)

    const otherType = lotteryType === "MegaMillion" ? "PowerBall" : "MegaMillion"
    const cachedOtherData = readCache()[otherType]
    if (!Array.isArray(cachedOtherData) || cachedOtherData.length === 0) {
      fetchData(otherType, { background: true })
    }

    return () => {
      ignore = true
    }
  }, [lotteryType])

  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentData = data.slice(indexOfFirstItem, indexOfLastItem)

  const totalPages = Math.ceil(data.length / itemsPerPage)
  const startPage = Math.max(1, currentPage - Math.floor(maxPageButtons / 2))
  const endPage = Math.min(totalPages, startPage + maxPageButtons - 1)
  const pageNumbers = Array.from({ length: endPage - startPage + 1 }, (_, index) => startPage + index)

  const handlePageChange = (pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setCurrentPage(pageNumber)
    }
  }

  const handleInputPageChange = (e) => {
    const page = Number.parseInt(e.target.value, 10)
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page)
    }
  }

  const handleLotteryTypeChange = (type) => {
    setLotteryType(type)
    setCurrentPage(1)
  }

  const { headers, fields } = tableConfig[lotteryType]
  const isPowerBall = lotteryType === "PowerBall"
  const showLoadingOverlay = loading
  const showEmptyState = !loading && !error && currentData.length === 0

  if (loading && isInitialLoad && data.length === 0) {
    return (
      <div className="history-numbers history-numbers-loading-view">
        <div className="history-loading-card">
          <div className="history-loading-spinner" />
          <h2>{isPowerBall ? "Loading Power Ball history..." : "Loading Mega Million history..."}</h2>
          <p>{isPowerBall ? "Power Ball data usually takes a bit longer. Please wait..." : "Preparing the latest draw history..."}</p>
        </div>
      </div>
    )
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="history-numbers">
      <button className="back-to-home-button" onClick={handleBackToHome}>
        ← Back to Generator
      </button>
      <h1>{lotteryType === "MegaMillion" ? "Mega Million Win History" : "Power Ball Win History"}</h1>
      <div className="button-group">
        <button
          className={`lottery-button ${lotteryType === "MegaMillion" ? "active" : ""}`}
          onClick={() => handleLotteryTypeChange("MegaMillion")}
        >
          Mega Ball
        </button>
        <button
          className={`lottery-button ${lotteryType === "PowerBall" ? "active" : ""}`}
          onClick={() => handleLotteryTypeChange("PowerBall")}
        >
          Power Ball
        </button>
      </div>
      <div className={`history-table-shell ${showLoadingOverlay ? "is-loading" : ""}`}>
        {showLoadingOverlay && (
          <div className="history-loading-overlay" aria-live="polite">
            <div className="history-loading-spinner" />
            <div className="history-loading-copy">
              <strong>{isPowerBall ? "Loading Power Ball history" : "Refreshing history numbers"}</strong>
              <span>
                {isPowerBall ? "Power Ball requests can take a little longer, but the page is still working." : "Fetching the latest results..."}
              </span>
            </div>
          </div>
        )}
      <div className="history-table-wrapper">
        <table className="history-table">
          <thead>
            <tr>
              {headers.map((header, index) => (
                <th key={index}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {currentData.map((draw, index) => (
              <tr key={index}>
                {fields.map((field, fieldIndex) => (
                  <td key={fieldIndex}>{draw[field] || "N/A"}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      </div>
      {showEmptyState && <div className="history-empty-state">No history data available right now.</div>}
      <div className="pagination">
        <button className="page-button" onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}>
          Previous
        </button>
        {pageNumbers.map((number) => (
          <button
            key={number}
            className={`page-button ${currentPage === number ? "active" : ""}`}
            onClick={() => handlePageChange(number)}
          >
            {number}
          </button>
        ))}
        <button
          className="page-button"
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
        >
          Next
        </button>
        <div className="jump-to-page">
          <span>Jump to page: </span>
          <input type="number" min="1" max={totalPages} onChange={handleInputPageChange} placeholder="Enter page" />
        </div>
      </div>
    </div>
  )
}

export default HistoryNumbers
