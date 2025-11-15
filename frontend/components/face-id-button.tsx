"use client";

import { useState, useEffect, useRef } from "react";

interface FaceIdButtonProps {
  onAuthSuccess?: () => void;
  onAuthStart?: () => void;
  autoStart?: boolean;
  className?: string;
}

export default function FaceIdButton({
  onAuthSuccess,
  onAuthStart,
  autoStart = false,
  className = "",
}: FaceIdButtonProps) {
  const [isActive, setIsActive] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const hasStartedRef = useRef(false);

  const startAnimation = () => {
    if (isActive || hasStartedRef.current) return;
    hasStartedRef.current = true;

    onAuthStart?.();
    setIsActive(true);

    // Complete animation after 1.7 seconds
    timerRef.current = setTimeout(() => {
      setIsCompleted(true);

      // Trigger success callback after checkmark animation
      setTimeout(() => {
        onAuthSuccess?.();
      }, 600);
    }, 1700);
  };

  const handleClick = () => {
    if (!autoStart) {
      startAnimation();
    }
  };

  useEffect(() => {
    if (autoStart) {
      // Start animation automatically after a short delay
      const autoStartTimer = setTimeout(() => {
        startAnimation();
      }, 300);

      return () => clearTimeout(autoStartTimer);
    }
  }, [autoStart]);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  return (
    <button
      onClick={handleClick}
      className={`face-id-wrapper ${isActive ? "active" : ""} ${isCompleted ? "completed" : ""} ${className}`}
      aria-label="Biometric Authentication"
      type="button"
      disabled={autoStart}
    >
      {/* Face ID Icon */}
      <svg
        className="face-id-default"
        version="1.1"
        viewBox="0 0 30 30"
        width="80"
        height="80"
      >
        <path
          d="M12.062 20c.688.5 1.688 1 2.938 1s2.25-.5 2.938-1M20 12v2M10 12v2M15 12v4a1 1 0 0 1-1 1"
          fill="none"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeMiterlimit="10"
        />
        <g
          fill="none"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeMiterlimit="10"
        >
          <path d="M26 9V6a2 2 0 0 0-2-2h-3M9 4H6a2 2 0 0 0-2 2v3M21 26h3a2 2 0 0 0 2-2v-3M4 21v3a2 2 0 0 0 2 2h3" />
        </g>
      </svg>

      {/* Animated Circles */}
      <div className="circle green"></div>
      <div className="circle blue"></div>
      <div className="circle purple"></div>

      {/* Checkmark */}
      <svg
        version="1.1"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 80 80"
        width="80"
        height="80"
      >
        <path
          className="path-tick"
          stroke="#FFF"
          strokeWidth="5"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M 25,45 35,55 60,30"
        />
      </svg>

      <style jsx>{`
        .face-id-wrapper {
          width: 80px;
          height: 80px;
          position: relative;
          cursor: pointer;
          transition: transform 0.2s;
        }

        .face-id-wrapper:disabled {
          cursor: default;
        }

        .face-id-wrapper:hover:not(.active):not(:disabled) {
          transform: scale(1.05);
        }

        .face-id-wrapper:active:not(.active):not(:disabled) {
          transform: scale(0.95);
        }

        .face-id-wrapper svg {
          position: absolute;
          top: 0;
          left: 0;
          fill: #94a3b8;
          stroke: #94a3b8;
        }

        .face-id-wrapper.active .face-id-default {
          opacity: 0;
          transform: scale(1.2);
          transition:
            opacity 1.5s,
            transform 1s;
          fill: #0ea5e9;
          stroke: #0ea5e9;
        }

        .circle {
          border-radius: 50%;
          border: 3px solid #000;
          width: 80px;
          height: 80px;
          background: transparent;
          box-sizing: border-box;
          position: absolute;
          top: 0;
          left: 0;
          opacity: 0;
        }

        .active .circle {
          opacity: 1;
          transition:
            opacity 0.7s,
            transform 2.2s;
        }

        .circle.green {
          border: 3px solid #88ef88;
        }

        .circle.blue {
          border: 3px solid #0aaaf7;
        }

        .circle.purple {
          border: 3px solid #ea54ea;
        }

        .active .circle.green {
          transform: rotateX(360deg);
        }

        .active .circle.blue {
          transform: rotateY(360deg);
        }

        .active .circle.purple {
          transform: rotateY(360deg) rotateX(360deg);
        }

        .completed .circle.purple {
          border: 3px solid #fff;
          transition: border 0.7s;
        }

        .path-tick {
          opacity: 0;
        }

        .completed .path-tick {
          stroke-dasharray: 49.497474670410156;
          stroke-dashoffset: 0;
          animation: dash 0.6s linear forwards;
          stroke-opacity: 1;
          opacity: 1;
        }

        @keyframes dash {
          0% {
            stroke-dashoffset: 49.497474670410156;
            stroke-opacity: 1;
          }
          60% {
            stroke-dashoffset: 49.497474670410156;
          }
          100% {
            stroke-dashoffset: 0;
            stroke-opacity: 1;
          }
        }
      `}</style>
    </button>
  );
}
