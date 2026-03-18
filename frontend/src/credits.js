const FREE_CREDITS_KEY = "freeCredits"
const PAID_CREDITS_KEY = "paidCredits"
const ACCESS_CODE_KEY = "accessCode"
const CREDITS_EVENT = "creditsUpdated"

const readInt = (key, fallback = 0) => {
  const rawValue = localStorage.getItem(key)
  const parsedValue = Number.parseInt(rawValue || "", 10)
  return Number.isNaN(parsedValue) ? fallback : parsedValue
}

export const getStoredCredits = () => {
  const freeCredits = readInt(FREE_CREDITS_KEY, 0)
  const paidCredits = readInt(PAID_CREDITS_KEY, 0)

  return {
    freeCredits,
    paidCredits,
    totalCredits: freeCredits + paidCredits,
  }
}

export const initializeCreditsIfNeeded = () => {
  const hasInitialized = localStorage.getItem("creditsInitialized")
  if (!hasInitialized) {
    localStorage.setItem(FREE_CREDITS_KEY, "5")
    localStorage.setItem(PAID_CREDITS_KEY, "0")
    localStorage.setItem("creditsInitialized", "true")
  }
}

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

export const setStoredCredits = ({ freeCredits, paidCredits }) => {
  localStorage.setItem(FREE_CREDITS_KEY, String(Math.max(0, freeCredits)))
  localStorage.setItem(PAID_CREDITS_KEY, String(Math.max(0, paidCredits)))
  emitCreditsUpdated()
}

export const setPaidCreditsOnly = (paidCredits) => {
  const { freeCredits } = getStoredCredits()
  setStoredCredits({ freeCredits, paidCredits })
}

export const setServerSyncedCredits = (remainingCredits) => {
  setStoredCredits({ freeCredits: 0, paidCredits: remainingCredits })
}

export const consumeStoredCredit = () => {
  const { freeCredits, paidCredits } = getStoredCredits()

  if (freeCredits > 0) {
    setStoredCredits({ freeCredits: freeCredits - 1, paidCredits })
    return freeCredits - 1 + paidCredits
  }

  if (paidCredits > 0) {
    setStoredCredits({ freeCredits, paidCredits: paidCredits - 1 })
    return freeCredits + paidCredits - 1
  }

  throw new Error("Insufficient credits")
}

export const getStoredAccessCode = () => localStorage.getItem(ACCESS_CODE_KEY) || ""

export const setStoredAccessCode = (accessCode) => {
  localStorage.setItem(ACCESS_CODE_KEY, accessCode)
}
