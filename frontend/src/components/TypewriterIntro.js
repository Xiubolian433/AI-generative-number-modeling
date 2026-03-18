"use client"

import { useState, useEffect } from "react"
import "./TypewriterIntro.css"

const TypewriterIntro = () => {
  const [displayedText, setDisplayedText] = useState("")
  const [currentIndex, setCurrentIndex] = useState(0)
  const [showCursor, setShowCursor] = useState(true)

  const fullText = `Welcome to the Future of Lottery AI Generator.
  
Our advanced GAN AI technology analyzes thousands of historical lottery numbers to identify hidden patterns and correlations. 

Using Generative Adversarial Networks, we generate numbers that closely resemble winning combinations from the past, giving you the edge in your lottery strategy.`

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
