"use client";

import React, { useRef, useEffect } from "react";

interface ParticlesProps {
  particleCount?: number;
  particleColors?: string[];
  particleSpread?: number;
  speed?: number;
  particleBaseSize?: number;
  moveParticlesOnHover?: boolean;
  particleHoverFactor?: number;
  alphaParticles?: boolean;
  disableRotation?: boolean;
  className?: string;
}

export default function Particles({
  particleCount = 200,
  particleColors = ["#ffffff", "#ffffff", "#ffffff"],
  particleSpread = 10,
  speed = 0.1,
  particleBaseSize = 100,
  moveParticlesOnHover = false,
  particleHoverFactor = 1,
  alphaParticles = false,
  disableRotation = false,
  className,
}: ParticlesProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let particles: Particle[] = [];
    let animationFrameId: number;
    let w = canvas.width;
    let h = canvas.height;

    // Handle resize
    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
      initParticles();
    };

    // Particle class
    class Particle {
      x: number;
      y: number;
      size: number;
      speedX: number;
      speedY: number;
      color: string;
      originalX: number;
      originalY: number;

      constructor() {
        this.x = Math.random() * w;
        this.y = Math.random() * h;
        this.originalX = this.x;
        this.originalY = this.y;
        this.size = Math.random() * (particleBaseSize / 100) + 1;
        this.speedX = (Math.random() - 0.5) * speed * 2;
        this.speedY = (Math.random() - 0.5) * speed * 2;
        this.color =
          particleColors[Math.floor(Math.random() * particleColors.length)];
      }

      update() {
        this.x += this.speedX;
        this.y += this.speedY;

        // Bounce off edges
        if (this.x > w || this.x < 0) this.speedX *= -1;
        if (this.y > h || this.y < 0) this.speedY *= -1;
      }

      draw() {
        if (!ctx) return;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        if (alphaParticles) {
          ctx.globalAlpha = Math.random() * 0.5 + 0.2;
        }
        ctx.fill();
        ctx.globalAlpha = 1;
      }
    }

    const initParticles = () => {
      particles = [];
      for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
      }
    };

    const animate = () => {
      if (!ctx) return;
      ctx.clearRect(0, 0, w, h);
      
      particles.forEach((particle) => {
        particle.update();
        particle.draw();
      });
      
      // Optional: Draw connections for "tech" feel
      connectParticles();

      animationFrameId = requestAnimationFrame(animate);
    };

    const connectParticles = () => {
        if (!ctx) return;
        const maxDistance = 100;
        for (let i = 0; i < particles.length; i++) {
            for (let j = i; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < maxDistance) {
                    ctx.beginPath();
                    ctx.strokeStyle = particleColors[0];
                    ctx.lineWidth = 0.5;
                    ctx.globalAlpha = 1 - distance / maxDistance; // Fade out
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                    ctx.globalAlpha = 1;
                }
            }
        }
    };

    window.addEventListener("resize", resize);
    resize();
    animate();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [
    particleCount,
    particleColors,
    speed,
    particleBaseSize,
    alphaParticles,
  ]);

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 z-0 h-full w-full pointer-events-none ${className}`}
    />
  );
}