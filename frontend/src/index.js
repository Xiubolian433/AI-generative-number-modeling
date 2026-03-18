import React from "react"
import ReactDOM from "react-dom/client"
import "./index.css"
import App from "./App"
import { tsParticles } from "@tsparticles/engine"
import { loadAll } from "@tsparticles/all"

const root = ReactDOM.createRoot(document.getElementById("root"))
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

const configs = {
  particles: {
    destroy: {
      mode: "split",
      split: {
        count: 1,
        factor: {
          value: {
            min: 2,
            max: 4,
          },
        },
        rate: {
          value: 100,
        },
        particles: {
          life: {
            count: 1,
            duration: {
              value: {
                min: 2,
                max: 3,
              },
            },
          },
          move: {
            speed: {
              min: 10,
              max: 15,
            },
          },
        },
      },
    },
    number: {
      value: 80,
    },
    color: {
      value: ["#3998D0", "#2EB6AF", "#A9BD33", "#FEC73B", "#F89930", "#F45623", "#D62E32", "#EB586E", "#9952CF"],
    },
    shape: {
      type: "circle",
    },
    opacity: {
      value: 1,
    },
    size: {
      value: {
        min: 10,
        max: 15,
      },
    },
    collisions: {
      enable: true,
      mode: "bounce",
    },
    move: {
      enable: true,
      speed: 3,
      outModes: "bounce",
    },
  },
  interactivity: {
    events: {
      onClick: {
        enable: true,
        mode: "pop",
      },
    },
  },
  background: {
    color: "#000000",
  },
}

window.onload = () => {
  document.body.style.zoom = "100%"
}

async function loadParticles(options) {
  await loadAll(tsParticles)
  await tsParticles.load({ id: "tsparticles", options })
}

loadParticles(configs)
