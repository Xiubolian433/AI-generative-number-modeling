"use client"

import { useEffect, useState } from "react"
import { Bar } from "react-chartjs-2"
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, Tooltip, Legend, Title } from "chart.js"
import "./HistoryStatistic.css"
import { useNavigate } from "react-router-dom"
import { API } from "../api.js"

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend, Title)

const HISTORY_STATISTICS_CACHE_KEY = "historyStatisticsCache"

const HistoryStatistic = () => {
  const navigate = useNavigate()
  const [statisticsType, setStatisticsType] = useState("MegaMillion")
  const [whiteBallOccurrences, setWhiteBallOccurrences] = useState({})
  const [specialBallOccurrences, setSpecialBallOccurrences] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isInitialLoad, setIsInitialLoad] = useState(true)

  const handleBackToHome = () => {
    navigate("/")
  }

  const readCache = () => {
    try {
      return JSON.parse(window.sessionStorage.getItem(HISTORY_STATISTICS_CACHE_KEY) || "{}")
    } catch (cacheError) {
      console.warn("Failed to read history statistics cache:", cacheError)
      return {}
    }
  }

  const writeCache = (type, nextData) => {
    try {
      const currentCache = readCache()
      window.sessionStorage.setItem(
        HISTORY_STATISTICS_CACHE_KEY,
        JSON.stringify({
          ...currentCache,
          [type]: nextData,
        }),
      )
    } catch (cacheError) {
      console.warn("Failed to write history statistics cache:", cacheError)
    }
  }

  const applyStatisticsData = (type, data) => {
    setWhiteBallOccurrences(data.whiteballoccurrences || {})

    if (type === "MegaMillion") {
      setSpecialBallOccurrences(data.megaBalloccurrences || {})
    } else {
      setSpecialBallOccurrences(data.powerballoccurrences || {})
    }
  }

  const fetchStatisticsData = async (type, options = {}) => {
    const { background = false, ignoreRef } = options
    let lastError = null

    const cachedData = readCache()[type]
    const hasCachedData = cachedData && typeof cachedData === "object" && Object.keys(cachedData).length > 0

    try {
      if (!background) {
        setLoading(true)
        setError(null)
        if (hasCachedData) {
          applyStatisticsData(type, cachedData)
          setIsInitialLoad(false)
        }
      }

      for (let attempt = 1; attempt <= 2; attempt += 1) {
        try {
          const response = await API.get(`/api/history-statistic/${type}`)
          const data = response.data

          writeCache(type, data)

          if (!background && !ignoreRef?.current) {
            applyStatisticsData(type, data)
            setIsInitialLoad(false)
          }

          return
        } catch (err) {
          lastError = err
          if (attempt < 2) {
            await new Promise((resolve) => setTimeout(resolve, 1500))
          }
        }
      }

      throw lastError || new Error("History statistics request failed")
    } catch (err) {
      console.error("Error fetching statistics data:", err)
      if (!background && !ignoreRef?.current) {
        setError(hasCachedData ? null : "Failed to fetch data. Please try again later.")
      }
    } finally {
      if (!background && !ignoreRef?.current) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    const ignoreRef = { current: false }

    fetchStatisticsData(statisticsType, { ignoreRef })

    const otherType = statisticsType === "MegaMillion" ? "PowerBall" : "MegaMillion"
    const cachedOtherData = readCache()[otherType]
    if (!cachedOtherData || Object.keys(cachedOtherData).length === 0) {
      fetchStatisticsData(otherType, { background: true, ignoreRef })
    }

    return () => {
      ignoreRef.current = true
    }
  }, [statisticsType])

  const handleButtonClick = (type) => {
    setStatisticsType(type)
  }

  const isPowerBall = statisticsType === "PowerBall"
  const isDataReady = Object.keys(whiteBallOccurrences).length > 0 || Object.keys(specialBallOccurrences).length > 0

  if (loading && isInitialLoad && !isDataReady) {
    return (
      <div className="history-statistic history-statistic-loading-view">
        <div className="history-loading-card">
          <div className="history-loading-spinner" />
          <h2>{isPowerBall ? "Loading Power Ball statistics..." : "Loading Mega Million statistics..."}</h2>
          <p>{isPowerBall ? "Power Ball frequency stats may take longer to prepare. Please wait..." : "Preparing the latest frequency charts..."}</p>
        </div>
      </div>
    )
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  const chartOptions = (xTitle, yTitle) => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "nearest",
      intersect: false,
      axis: "x",
    },
    layout: {
      padding: {
        bottom: 15,
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: xTitle,
          color: "white",
          font: {
            size: 16,
            weight: "bold",
          },
          padding: {
            top: 8,
          },
        },
        ticks: {
          color: "white",
          font: {
            size: 14,
          },
          padding: 8,
          maxRotation: 0,
          minRotation: 0,
        },
        grid: {
          color: "rgba(255, 255, 255, 0.2)",
        },
      },
      y: {
        title: {
          display: true,
          text: yTitle,
          color: "white",
          font: {
            size: 16,
            weight: "bold",
          },
        },
        ticks: {
          color: "white",
          font: {
            size: 14,
          },
          padding: 8,
        },
        grid: {
          color: "rgba(255, 255, 255, 0.1)",
        },
      },
    },
    plugins: {
      legend: {
        labels: {
          color: "white",
          font: {
            size: 14,
            weight: "bold",
          },
          padding: 20,
        },
      },
      tooltip: {
        mode: "nearest",
        intersect: false,
        axis: "x",
        backgroundColor: "rgba(0, 0, 0, 0.8)",
        titleColor: "white",
        bodyColor: "white",
        borderColor: "rgba(255, 255, 255, 0.3)",
        borderWidth: 1,
        titleFont: {
          size: 14,
          weight: "bold",
        },
        bodyFont: {
          size: 13,
        },
        padding: 10,
        cornerRadius: 6,
        displayColors: true,
        callbacks: {
          title: (context) => `Ball Number: ${context[0].label}`,
          label: (context) => `Frequency: ${context.raw}`,
        },
        position: "nearest",
      },
    },
    onHover: (event, activeElements) => {
      event.native.target.style.cursor = activeElements.length > 0 ? "pointer" : "default"
    },
    elements: {
      bar: {
        borderWidth: 1,
        borderRadius: 2,
        hoverBorderWidth: 2,
      },
    },
  })

  const whiteBallData = {
    labels: Object.keys(whiteBallOccurrences),
    datasets: [
      {
        label: "White Ball Frequency",
        data: Object.values(whiteBallOccurrences),
        backgroundColor: statisticsType === "MegaMillion" ? "rgba(255, 204, 0, 0.8)" : "rgba(255, 0, 0, 0.8)",
        hoverBackgroundColor: statisticsType === "MegaMillion" ? "rgba(255, 204, 0, 1)" : "rgba(255, 0, 0, 1)",
        borderColor: statisticsType === "MegaMillion" ? "rgba(255, 204, 0, 1)" : "rgba(255, 0, 0, 1)",
        borderWidth: 1,
        pointHoverRadius: 8,
      },
    ],
  }

  const specialBallData = {
    labels: Object.keys(specialBallOccurrences),
    datasets: [
      {
        label: `${statisticsType === "MegaMillion" ? "Mega Ball Frequency" : "Power Ball Frequency"}`,
        data: Object.values(specialBallOccurrences),
        backgroundColor: statisticsType === "MegaMillion" ? "rgba(75, 192, 192, 0.8)" : "rgba(255, 255, 255, 0.8)",
        hoverBackgroundColor: statisticsType === "MegaMillion" ? "rgba(75, 192, 192, 1)" : "rgba(255, 255, 255, 1)",
        borderColor: statisticsType === "MegaMillion" ? "rgba(75, 192, 192, 1)" : "rgba(255, 255, 255, 1)",
        borderWidth: 1,
        pointHoverRadius: 8,
      },
    ],
  }

  return (
    <div className="history-statistic">
      <button className="back-to-home-button" onClick={handleBackToHome}>
        ← Back to Generator
      </button>
      <h1>Lottery History Frequency Statistics</h1>
      <div className="history-button-container">
        <button
          className={`toggle-button ${statisticsType === "MegaMillion" ? "active" : ""}`}
          onClick={() => handleButtonClick("MegaMillion")}
        >
          Mega Million
        </button>
        <button
          className={`toggle-button ${statisticsType === "PowerBall" ? "active" : ""}`}
          onClick={() => handleButtonClick("PowerBall")}
        >
          Power Ball
        </button>
      </div>
      {loading && (
        <div className="history-loading-inline" aria-live="polite">
          <div className="history-loading-spinner compact" />
          <span>
            {isPowerBall
              ? "Loading Power Ball statistics. This request is usually slower."
              : "Refreshing statistics..."}
          </span>
        </div>
      )}
      <div className={`chart-shell ${loading ? "is-loading" : ""}`}>
      <div className="chart-container">
        <h2>White Ball Frequencies</h2>
        <Bar data={whiteBallData} options={chartOptions("Ball Number", "Frequency")} />
      </div>
      <div className="chart-container">
        <h2>{statisticsType === "MegaMillion" ? "Mega Ball Frequencies" : "Power Ball Frequencies"}</h2>
        <Bar data={specialBallData} options={chartOptions("Ball Number", "Frequency")} />
      </div>
      </div>
    </div>
  )
}

export default HistoryStatistic
