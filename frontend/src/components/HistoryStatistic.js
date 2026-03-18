"use client"

import { useEffect, useState } from "react"
import { Bar } from "react-chartjs-2"
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, Tooltip, Legend, Title } from "chart.js"
import "./HistoryStatistic.css"
import { useNavigate } from "react-router-dom"
import { API } from "../api.js"

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend, Title)

const HistoryStatistic = () => {
  const navigate = useNavigate()
  const [statisticsType, setStatisticsType] = useState("MegaMillion")
  const [whiteBallOccurrences, setWhiteBallOccurrences] = useState({})
  const [specialBallOccurrences, setSpecialBallOccurrences] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const handleBackToHome = () => {
    navigate("/")
  }

  const fetchStatisticsData = async (type) => {
    let lastError = null

    try {
      setLoading(true)
      setError(null)
      for (let attempt = 1; attempt <= 2; attempt += 1) {
        try {
          const response = await API.get(`/api/history-statistic/${type}`)
          const data = response.data

          setWhiteBallOccurrences(data.whiteballoccurrences || {})

          if (type === "MegaMillion") {
            setSpecialBallOccurrences(data.megaBalloccurrences || {})
          } else if (type === "PowerBall") {
            setSpecialBallOccurrences(data.powerballoccurrences || {})
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
      setError("Failed to fetch data. Please try again later.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatisticsData(statisticsType)
  }, [statisticsType])

  const handleButtonClick = (type) => {
    setStatisticsType(type)
  }

  if (loading) {
    return <div className="loading">Loading...</div>
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
      <div className="chart-container">
        <h2>White Ball Frequencies</h2>
        <Bar data={whiteBallData} options={chartOptions("Ball Number", "Frequency")} />
      </div>
      <div className="chart-container">
        <h2>{statisticsType === "MegaMillion" ? "Mega Ball Frequencies" : "Power Ball Frequencies"}</h2>
        <Bar data={specialBallData} options={chartOptions("Ball Number", "Frequency")} />
      </div>
    </div>
  )
}

export default HistoryStatistic
