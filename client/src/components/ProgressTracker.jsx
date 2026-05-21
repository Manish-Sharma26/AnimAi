/**
 * ProgressTracker — Animated progress steps for video generation
 * 
 * Shows 4 stages: Planning → Coding → Compiling → Uploading
 * Each step lights up as the worker emits progress events.
 */

const STAGES = [
  { key: "planning", label: "Planning", icon: "🧠", percent: 20 },
  { key: "compiling", label: "Generating", icon: "⚡", percent: 60 },
  { key: "uploading", label: "Uploading", icon: "☁️", percent: 80 },
  { key: "complete", label: "Complete", icon: "✅", percent: 100 },
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
        {STAGES.map((stage, i) => (
          <div
            key={stage.key}
            className={`progress-tracker__step ${
              i <= activeIdx ? "progress-tracker__step--active" : ""
            } ${stage.key === currentStep ? "progress-tracker__step--current" : ""}`}
          >
            <span className="progress-tracker__icon">{stage.icon}</span>
            <span className="progress-tracker__label">{stage.label}</span>
          </div>
        ))}
      </div>

      <p className="progress-tracker__percent">{percent || 0}%</p>
    </div>
  );
}
