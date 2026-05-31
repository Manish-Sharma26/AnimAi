/**
 * ProgressTracker — Animated progress steps for video generation
 * 
 * Shows 6 stages matching the Python pipeline:
 *   Planning → Coding → Compiling → Debugging (if needed) → Uploading → Complete
 * 
 * The progress bar smoothly animates between stages.
 */

const STAGES = [
  { key: "planning", label: "Planning", icon: "🧠" },
  { key: "coding", label: "Coding", icon: "💻" },
  { key: "compiling", label: "Compiling", icon: "⚡" },
  { key: "debugging", label: "Debugging", icon: "🔧" },
  { key: "uploading", label: "Uploading", icon: "☁️" },
  { key: "complete", label: "Complete", icon: "✅" },
];

export default function ProgressTracker({ currentStep, percent }) {
  const activeIdx = STAGES.findIndex((s) => s.key === currentStep);

  return (
    <div className="progress-tracker">
      <div className="progress-tracker__bar">
        <div
          className="progress-tracker__fill"
          style={{ width: `${percent || 0}%` }}
        />
      </div>

      <div className="progress-tracker__steps">
        {STAGES.map((stage, i) => {
          // Skip debugging if we've passed it without hitting it
          if (stage.key === "debugging" && activeIdx > i && currentStep !== "debugging") {
            return null;
          }
          return (
            <div
              key={stage.key}
              className={`progress-tracker__step ${
                i <= activeIdx ? "progress-tracker__step--active" : ""
              } ${stage.key === currentStep ? "progress-tracker__step--current" : ""}`}
            >
              <span className="progress-tracker__icon">{stage.icon}</span>
              <span className="progress-tracker__label">{stage.label}</span>
            </div>
          );
        })}
      </div>

      <p className="progress-tracker__percent">{percent || 0}%</p>
    </div>
  );
}
