"use client";

import { useState, useEffect, useRef } from "react";
import { projects, Project } from "@/lib/projects";

// cos(65°) ≈ 0.423 — compresses the Y axis to simulate a 65° tilt
const TILT = 0.423;

const orbitConfig = [
  { rx: 290, period: 28000, startAngle: 0 },
  { rx: 410, period: 44000, startAngle: 2.094 },  // 120°
  { rx: 530, period: 65000, startAngle: 4.189 },  // 240°
];

const statusConfig = {
  live:          { label: "LIVE",         color: "text-green-400", dot: "bg-green-400", glow: "0 0 16px 5px rgba(74,222,128,0.7)"  },
  "in-progress": { label: "IN PROGRESS",  color: "text-amber-400", dot: "bg-amber-400", glow: "0 0 16px 5px rgba(245,166,35,0.7)"  },
  "coming-soon": { label: "COMING SOON",  color: "text-gray-500",  dot: "bg-gray-500",  glow: "0 0 16px 5px rgba(107,114,128,0.4)" },
};

export default function OrbitalSystem() {
  const [selected, setSelected] = useState<Project | null>(null);
  const [angles, setAngles] = useState(orbitConfig.map((o) => o.startAngle));
  const lastTimeRef = useRef<number | null>(null);
  const rafRef = useRef<number>();

  useEffect(() => {
    const animate = (time: number) => {
      if (lastTimeRef.current === null) lastTimeRef.current = time;
      const dt = time - lastTimeRef.current;
      lastTimeRef.current = time;

      setAngles((prev) =>
        prev.map((angle, i) => angle + (2 * Math.PI * dt) / orbitConfig[i].period)
      );

      rafRef.current = requestAnimationFrame(animate);
    };

    rafRef.current = requestAnimationFrame(animate);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return (
    <>
      {/* ── Modal ───────────────────────────────────────────────── */}
      {selected && (
        <div
          className="fixed inset-0 z-[200] flex items-end justify-center"
          onClick={() => setSelected(null)}
        >
          <div className="absolute inset-0" style={{ background: "rgba(7,7,15,0.7)" }} />
          <div
            className="relative w-full max-w-2xl p-10"
            style={{
              background: "rgba(7,7,15,0.98)",
              border: "1px solid rgba(245,166,35,0.2)",
              borderBottom: "none",
              animation: "slide-up 0.35s ease forwards",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Corner accents */}
            <div className="absolute top-3 left-3 w-4 h-4" style={{ borderTop: "1px solid rgba(245,166,35,0.4)", borderLeft: "1px solid rgba(245,166,35,0.4)" }} />
            <div className="absolute top-3 right-3 w-4 h-4" style={{ borderTop: "1px solid rgba(245,166,35,0.4)", borderRight: "1px solid rgba(245,166,35,0.4)" }} />

            <button
              onClick={() => setSelected(null)}
              className="absolute top-5 right-8 text-gray-700 hover:text-amber-400 transition-colors text-xs tracking-[0.3em]"
              style={{ fontFamily: "var(--font-orbitron)" }}
            >
              CLOSE ✕
            </button>

            <div className="flex items-center gap-2 mb-4">
              <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${statusConfig[selected.status].dot}`} />
              <span className={`text-xs tracking-[0.3em] ${statusConfig[selected.status].color}`} style={{ fontFamily: "var(--font-orbitron)" }}>
                {statusConfig[selected.status].label}
              </span>
            </div>

            <h2 className="text-2xl text-white tracking-[0.2em] mb-3" style={{ fontFamily: "var(--font-orbitron)" }}>
              {selected.name}
            </h2>
            <div className="w-12 h-px bg-amber-400 opacity-20 mb-5" />
            <p className="text-gray-500 text-sm leading-relaxed mb-6">{selected.description}</p>

            <div className="flex flex-wrap gap-2 mb-8">
              {selected.tech.map((t) => (
                <span
                  key={t}
                  className="text-xs px-2 py-1 text-gray-600 tracking-wider"
                  style={{ border: "1px solid rgba(255,255,255,0.06)" }}
                >
                  {t}
                </span>
              ))}
            </div>

            <div className="flex gap-8">
              {selected.liveUrl ? (
                <a
                  href={selected.liveUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs tracking-[0.3em] text-amber-400 hover:text-white transition-colors"
                  style={{ fontFamily: "var(--font-orbitron)" }}
                >
                  LIVE APP →
                </a>
              ) : (
                <span className="text-xs tracking-[0.3em] text-gray-700" style={{ fontFamily: "var(--font-orbitron)" }}>
                  DEPLOYING...
                </span>
              )}
              <a
                href={selected.githubUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs tracking-[0.3em] text-gray-500 hover:text-white transition-colors"
                style={{ fontFamily: "var(--font-orbitron)" }}
              >
                GITHUB →
              </a>
            </div>
          </div>
        </div>
      )}

      {/* ── Orbital system ──────────────────────────────────────── */}
      <div className="absolute inset-0 flex items-center justify-center" style={{ zIndex: 2 }}>

        {/* SVG rings — pure visual, no pointer events */}
        <svg
          style={{
            position: "absolute",
            width: "1200px",
            height: "700px",
            overflow: "visible",
            pointerEvents: "none",
          }}
          viewBox="-600 -350 1200 700"
        >
          {orbitConfig.map((orbit, i) => (
            <ellipse
              key={i}
              cx={0}
              cy={0}
              rx={orbit.rx}
              ry={orbit.rx * TILT}
              fill="none"
              stroke={`rgba(245,166,35,${0.18 - i * 0.04})`}
              strokeWidth={1}
              style={{ filter: `drop-shadow(0 0 6px rgba(245,166,35,${0.06 - i * 0.01}))` }}
            />
          ))}
        </svg>

        {/* Orbiting nodes — flat HTML, z-sorted by depth */}
        {projects
          .map((project, i) => {
            const orbit = orbitConfig[i];
            const x = orbit.rx * Math.cos(angles[i]);
            const y = orbit.rx * TILT * Math.sin(angles[i]);
            // depth: nodes "behind" centre get lower z-index
            const depth = Math.sin(angles[i]);
            const status = statusConfig[project.status];
            return { project, x, y, depth, status };
          })
          .sort((a, b) => a.depth - b.depth) // paint back-to-front
          .map(({ project, x, y, depth, status }) => (
            <div
              key={project.id}
              style={{
                position: "absolute",
                transform: `translate(${x}px, ${y}px)`,
                zIndex: depth > 0 ? 8 : 4,
              }}
            >
              <div
                onClick={() => setSelected(project)}
                className="group flex flex-col items-center gap-3"
                style={{
                  cursor: "none",
                  transform: "translate(-50%, -50%)",
                  // subtle scale: nodes "closer" appear slightly larger
                  scale: String(0.88 + depth * 0.12),
                  transition: "scale 0.1s linear",
                }}
              >
                {/* Glowing dot */}
                <div className="relative flex items-center justify-center">
                  <div
                    className="absolute rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    style={{
                      width: "56px",
                      height: "56px",
                      border: `1px solid ${project.status === "live" ? "rgba(74,222,128,0.5)" : "rgba(245,166,35,0.5)"}`,
                      animation: "ping 1.5s ease infinite",
                    }}
                  />
                  <div
                    className="absolute rounded-full"
                    style={{
                      width: "38px",
                      height: "38px",
                      border: `1px solid ${project.status === "live" ? "rgba(74,222,128,0.25)" : "rgba(245,166,35,0.25)"}`,
                    }}
                  />
                  <div
                    className="rounded-full transition-all duration-300 group-hover:scale-150"
                    style={{
                      width: "22px",
                      height: "22px",
                      background:
                        project.status === "live"
                          ? "radial-gradient(circle, #4ade80 0%, rgba(74,222,128,0.5) 100%)"
                          : "radial-gradient(circle, #f5a623 0%, rgba(245,166,35,0.5) 100%)",
                      boxShadow: status.glow,
                    }}
                  />
                </div>

                {/* Label */}
                <div
                  className="flex flex-col items-center gap-1 px-4 py-2"
                  style={{
                    background: "rgba(4,4,12,0.95)",
                    border: `1px solid ${project.status === "live" ? "rgba(74,222,128,0.2)" : "rgba(245,166,35,0.2)"}`,
                  }}
                >
                  <span
                    className={`whitespace-nowrap font-bold group-hover:text-amber-400 transition-colors ${project.status === "live" ? "text-green-400" : "text-white"}`}
                    style={{ fontFamily: "var(--font-orbitron)", fontSize: "11px", letterSpacing: "0.15em" }}
                  >
                    {project.name.toUpperCase()}
                  </span>
                  <span
                    className={statusConfig[project.status].color}
                    style={{ fontFamily: "var(--font-orbitron)", fontSize: "8px", letterSpacing: "0.2em" }}
                  >
                    {statusConfig[project.status].label}
                  </span>
                </div>
              </div>
            </div>
          ))}

        {/* ── Black hole ──────────────────────────────────────────── */}
        <div className="absolute flex items-center justify-center" style={{ zIndex: 10, pointerEvents: "none" }}>
          <div
            className="absolute rounded-full"
            style={{
              width: "340px",
              height: "340px",
              border: "1px solid rgba(245,166,35,0.07)",
              boxShadow: "0 0 60px 20px rgba(245,166,35,0.03)",
            }}
          />
          <div
            className="absolute rounded-full"
            style={{
              width: "310px",
              height: "310px",
              background: "radial-gradient(circle, rgba(245,166,35,0.05) 0%, transparent 70%)",
            }}
          />
          <div
            className="rounded-full flex flex-col items-center justify-center gap-2"
            style={{
              width: "270px",
              height: "270px",
              background: "radial-gradient(circle, #020207 55%, #07070f 100%)",
              boxShadow: "0 0 100px 50px #07070f",
            }}
          >
            <p className="text-gray-800 text-xs tracking-[0.5em]" style={{ fontFamily: "var(--font-orbitron)" }}>
              MISSION
            </p>
            <h1 className="text-3xl font-bold tracking-widest text-amber-400 glow-amber" style={{ fontFamily: "var(--font-orbitron)" }}>
              DENZOS
            </h1>
            <p className="text-gray-800 text-xs tracking-widest" style={{ fontFamily: "var(--font-orbitron)" }}>
              DENZ-001
            </p>
          </div>
        </div>

      </div>
    </>
  );
}
