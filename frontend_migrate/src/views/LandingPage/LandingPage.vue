<template>
  <div class="landing">
    <!-- ── NAV ── -->
    <nav class="landing-nav">
      <RouterLink class="landing-nav-logo" to="/">
        <div class="landing-nav-logo-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--md-primary)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
          </svg>
        </div>
        <span class="landing-nav-logo-name">KnowWatt</span>
      </RouterLink>
      <div class="landing-nav-actions">
        <RouterLink to="/login" class="btn-text" style="height:36px;line-height:36px;">Sign In</RouterLink>
        <RouterLink to="/register" class="btn-filled" style="height:36px;line-height:36px;padding:0 20px;">Get Started</RouterLink>
      </div>
    </nav>

    <!-- ── HERO ── -->
    <section class="hero m3-enter">
      <div class="hero-eyebrow">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
        Smart Energy Monitoring
      </div>

      <h1 class="hero-title">
        Know your watts.<br>
        <span class="accent">Save your money.</span>
      </h1>

      <p class="hero-sub">
        KnowWatt gives you real-time visibility into every smart plug in your home.
        Track usage, set timers, get alerts — and cut your electricity bill effortlessly.
      </p>

      <div class="hero-actions">
        <RouterLink to="/register" class="btn-filled" style="height:48px;line-height:48px;padding:0 32px;font-size:var(--type-body-lg);">
          Start for free
        </RouterLink>
        <RouterLink to="/login" class="btn-tonal" style="height:48px;line-height:48px;padding:0 32px;font-size:var(--type-body-lg);">
          Sign in
        </RouterLink>
      </div>
    </section>

    <!-- ── STATS STRIP ── -->
    <div class="stats-strip m3-enter d2">
      <div class="stat-item">
        <div class="stat-num">12.5<span style="font-size:var(--type-title-md);font-weight:400"> kWh</span></div>
        <div class="stat-desc">Average daily usage tracked</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">30%</div>
        <div class="stat-desc">Average energy savings reported</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">7</div>
        <div class="stat-desc">Plugs monitored per household</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">Real-time</div>
        <div class="stat-desc">Live power consumption data</div>
      </div>
    </div>

    <!-- ── FEATURES ── -->
    <section class="features m3-enter d3">
      <h2 class="features-title">Everything you need</h2>
      <p class="features-sub">Simple, powerful tools to understand and control your energy use</p>

      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon primary">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--md-primary)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="20" x2="18" y2="10"/>
              <line x1="12" y1="20" x2="12" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
          </div>
          <div class="feature-name">Real-time Monitoring</div>
          <div class="feature-desc">See live power draw from every plug. Spot energy hogs instantly and understand your usage patterns over time.</div>
        </div>

        <div class="feature-card">
          <div class="feature-icon secondary">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--md-secondary)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
          </div>
          <div class="feature-name">Smart Alerts</div>
          <div class="feature-desc">Get notified when a device runs too long, draws unusual power, or goes offline. Stay in control without watching a screen.</div>
        </div>

        <div class="feature-card">
          <div class="feature-icon tertiary">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--md-tertiary)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <rect x="6" y="2" width="12" height="6" rx="2"/>
              <path d="M4 8h16v2a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4V8z"/>
              <path d="M12 14v8"/>
            </svg>
          </div>
          <div class="feature-name">Remote Control</div>
          <div class="feature-desc">Turn any plug on or off from anywhere. Schedule devices, set timers, and automate your home's energy routine.</div>
        </div>
      </div>
    </section>

    <!-- ── CTA ── -->
    <section class="cta-section m3-enter d4">
      <h2 class="cta-title">Ready to take control of your energy?</h2>
      <p class="cta-sub">Create a free account and connect your first smart plug in minutes.</p>
      <RouterLink to="/register" class="btn-filled" style="height:48px;line-height:48px;padding:0 36px;font-size:var(--type-body-lg);background:var(--md-primary);">
        Create free account
      </RouterLink>
    </section>

    <!-- ── FOOTER ── -->
    <footer class="landing-footer">
      <span class="footer-copy">© 2025 KnowWatt. All rights reserved.</span>
      <div class="footer-links">
        <RouterLink to="/login">Sign In</RouterLink>
        <RouterLink to="/register">Register</RouterLink>
        <RouterLink to="/forgot-password">Forgot Password</RouterLink>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>

<style scoped>
@import './LandingPage.css';
</style>
