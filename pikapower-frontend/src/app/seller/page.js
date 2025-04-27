"use client";
import "./page.css";
import pikachu from "@/assets/pikachu_sitting.png";
import pikachu_electric from "@/assets/pikachu_electric.png";
import { useState, useEffect } from "react";
import Image from "next/image";
import { io } from "socket.io-client";

// Connect to backend WebSocket
const socket = io("http://192.168.137.2:5000");

export default function Buyer() {
  const [charging, setCharging] = useState(false);
  const [battery, setBattery] = useState(75);

  useEffect(() => {
    socket.on("charging_status", (data) => {
      console.log(data); // for debugging

      if (data.status === "Charging") {
        setCharging(true);
        setBattery((prev) => Math.min(prev + 1, 100)); // Slowly increase battery
      } else if (data.status === "Not Charging") {
        setCharging(false);
      }
    });

    return () => {
      socket.off("charging_status");
    };
  }, []);

  return (
    <div className="buyer-container">
      <div className="buyer-logs">
        <center>
          <h1>Logs</h1>
        </center>
        <ul className="buyer-logs-list">
          <li>Trade with vrush1234(1:30)</li>
          <li>Trade with vrush1234(2:30)</li>
          <li>Trade with vrush1234(3:30)</li>
          <li>Trade with vrush1234(4:30)</li>
          <li>Trade with vrush1234(5:30)</li>
          <li>Trade with vrush1234(6:30)</li>
          <li>Trade with vrush1234(7:30)</li>
          <li>Trade with vrush1234(8:30)</li>
          <li>Trade with vrush1234(9:30)</li>
        </ul>
      </div>
      <div className="buyer-right">
        <div
          className="current-state"
          style={{ backgroundColor: charging ? "rgb(234, 179, 0)" : "white" }}
        >
          <h1>Current State</h1>
          <div className="state-img-container">
            <Image
              src={charging ? pikachu_electric : pikachu}
              alt="Pikachu"
              fill
            />
          </div>
          <h2>{charging ? "Charging" : "Not Charging"}</h2>
        </div>
        <div className="battery-percentage">
          <h1>Battery Percentage</h1>
          <div className="battery">
            <div
              className="battery-fill"
              style={{ width: battery + "%" }}
            ></div>
          </div>
          <h2>{battery + "%"}</h2>
        </div>
      </div>
    </div>
  );
}
