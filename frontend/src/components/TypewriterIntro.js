"use client"

import { useState, useEffect } from "react"
import "./TypewriterIntro.css"

const TypewriterIntro = () => {
  const [displayedText, setDisplayedText] = useState("")
  const [currentIndex, setCurrentIndex] = useState(0)
  const [showCursor, setShowCursor] = useState(true)

  const fullText = `Welcome to the Future of Lottery AI Generator.

Our AI lottery number generator uses GAN models and historical draw analysis to create smart picks for Mega Millions and Powerball.

Explore lottery history numbers, view lottery frequency statistics, and generate AI-assisted number combinations in one place.`

  useEffect(() => {
    if (currentIndex < fullText.length) {
      const timer = setTimeout(() => {
        setDisplayedText((prev) => prev + fullText[currentIndex])
        setCurrentIndex((prev) => prev + 1)
      }, 50) // 调整打字速度，50ms每个字符

      return () => clearTimeout(timer)
    }
  }, [currentIndex, fullText])

  useEffect(() => {
    // 光标闪烁效果
    const cursorTimer = setInterval(() => {
      setShowCursor((prev) => !prev)
    }, 500)

    return () => clearInterval(cursorTimer)
  }, [])

  return (
    <div className="typewriter-intro">
      <div className="typewriter-content">
        <span className="typewriter-text">{displayedText}</span>
        <span className={`typewriter-cursor ${showCursor ? "visible" : "hidden"}`}>|</span>
      </div>
    </div>
  )
}

export default TypewriterIntro
