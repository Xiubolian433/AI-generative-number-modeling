const TOTAL_CREDITS_KEY = "totalCredits"
const ACCESS_CODE_KEY = "accessCode"
const CREDITS_EVENT = "creditsUpdated"

const readInt = (key, fallback = 0) => {
  const rawValue = localStorage.getItem(key)
  const parsedValue = Number.parseInt(rawValue || "", 10)
  return Number.isNaN(parsedValue) ? fallback : parsedValue
}

export const getStoredCredits = () => {
  const totalCredits = readInt(TOTAL_CREDITS_KEY, 0)

  return {
    freeCredits: 0,
    paidCredits: totalCredits,
    totalCredits,
  }
}

export const initializeCreditsIfNeeded = () => {}

export const emitCreditsUpdated = () => {
  window.dispatchEvent(new Event(CREDITS_EVENT))
}

export const subscribeToCreditsUpdated = (listener) => {
  window.addEventListener("storage", listener)
  window.addEventListener(CREDITS_EVENT, listener)

  return () => {
    window.removeEventListener("storage", listener)
    window.removeEventListener(CREDITS_EVENT, listener)
  }
}

export const setStoredCredits = ({ totalCredits }) => {
  localStorage.setItem(TOTAL_CREDITS_KEY, String(Math.max(0, totalCredits)))
  emitCreditsUpdated()
}

export const setServerSyncedCredits = (remainingCredits) => {
  setStoredCredits({ totalCredits: remainingCredits })
}

export const getStoredAccessCode = () => localStorage.getItem(ACCESS_CODE_KEY) || ""

export const setStoredAccessCode = (accessCode) => {
  if (accessCode) {
    localStorage.setItem(ACCESS_CODE_KEY, accessCode)
  } else {
    localStorage.removeItem(ACCESS_CODE_KEY)
  }
}
