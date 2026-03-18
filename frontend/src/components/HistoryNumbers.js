"use client"

import { useState, useEffect } from "react"
import "./HistoryNumbers.css"
import { useNavigate } from "react-router-dom"
import { API } from "../api.js"

const HistoryNumbers = () => {
  const [data, setData] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [lotteryType, setLotteryType] = useState("MegaMillion")

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

  const handleBackToHome = () => {
    navigate("/")
  }

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const response = await API.get(`/api/history-numbers/${lotteryType}`)
        setData(response.data)
      } catch (error) {
        console.error("Error fetching data:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
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

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  const { headers, fields } = tableConfig[lotteryType]

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
