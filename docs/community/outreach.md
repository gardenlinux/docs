---
title: Community Outreach
description: Mailing lists, chat rooms, and meetings for the Garden Linux community
order: 3
---

# Community Outreach

Garden Linux is built in the open by contributors, maintainers, and users around
the world. Pick the channel that fits what you need — from long-form project
discussions to quick questions and recurring community calls.

This page is part of the [Community overview](./index.md). See also the
[Charter](./charter.md) and [Members](./members.md).

::: info Draft page
This page is a draft. Entries marked **Placeholder** still need a final,
confirmed link or schedule before this page is published.
:::

<div class="community-grid">
  <section class="community-card">
    <span class="community-kicker">Stay informed</span>
    <h2>Mailing Lists</h2>
    <p>
      Subscribe to our mailing lists to stay up-to-date with recent news about Gardenlinux.
    </p>
    <ul class="community-list">
      <li>
        <a href="https://lists.neonephos.org/g/gardenlinux-discussion">gardenlinux-discussion</a>
        <span>General news, release announcements, and project discussion.</span>
      </li>
      <li>
        <a href="https://lists.neonephos.org/g/gardenlinux-security">gardenlinux-security</a>
        <span>Security announcements and public security coordination.</span>
      </li>
      <li>
        <a href="https://lists.neonephos.org/g/gardenlinux-security-embargo">gardenlinux-security-embargo</a>
        <span>Private coordination for embargoed security topics.</span>
      </li>
    </ul>
  </section>

  <section class="community-card">
    <span class="community-kicker">Talk to people</span>
    <h2>Community Messaging</h2>
    <p>
      Real-time chat for questions, debugging help, and day-to-day coordination
      between contributors.
    </p>
    <ul class="community-list">
      <li>
        <a href="https://matrix.to/#/#gardenlinux:matrix.org">#gardenlinux:matrix.org</a>
        <span class="community-badge">Placeholder</span>
        <span>Main project room for general questions and discussion.</span>
      </li>
      <li>
        <a href="https://matrix.to/#/#gardenlinux-dev:matrix.org">#gardenlinux-dev:matrix.org</a>
        <span class="community-badge">Placeholder</span>
        <span>Development-focused room for code and build topics.</span>
      </li>
      <li>
        <a href="https://matrix.to/#/#gardenlinux-docs:matrix.org">#gardenlinux-docs:matrix.org</a>
        <span class="community-badge">Placeholder</span>
        <span>Documentation contributors and review coordination.</span>
      </li>
    </ul>
  </section>

  <section class="community-card">
    <span class="community-kicker">Meet the project</span>
    <h2>Community Meeting</h2>
    <p>
      Join our community meeting.
    </p>
    <ul class="community-list">
      <li>
        <strong>When</strong>
        <span class="community-badge">Placeholder</span>
        <span>Day, Time</span>
      </li>
      <li>
        <strong>Where</strong>
        <span class="community-badge">Placeholder</span>
        <span><a href="#">Join via Teams</a></span>
      </li>
      <li>
        <strong>Agenda</strong>
        <span class="community-badge">Placeholder</span>
        <span>Published in the mailing list before each meeting.</span>
      </li>
    </ul>
    <a class="community-cta" href="https://lists.neonephos.org/g/gardenlinux-discussion">
      Get the meeting announcement
    </a>
  </section>
</div>

## Get Involved

The fastest way to get involved is to introduce yourself on the mailing list or
say hello in a Matrix room, then look for a first issue to work on.

<div class="community-cta-row">
  <a class="community-cta" href="/contributing/">Read the contributing guide</a>
  <a class="community-cta secondary" href="https://github.com/gardenlinux/gardenlinux/issues">
    Browse open issues
  </a>
</div>

<style scoped>
.community-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
  margin: 2rem 0;
}

.community-card {
  display: flex;
  flex-direction: column;
  padding: 1.25rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  background-color: var(--vp-c-bg-soft);
}

.community-kicker {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--vp-c-brand-1);
}

.community-card h2 {
  margin: 0.25rem 0 0.5rem;
  padding-top: 0;
  border-top: 0;
  font-size: 1.25rem;
}

.community-card p {
  margin: 0 0 1rem;
  color: var(--vp-c-text-2);
}

.community-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.community-list li {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--vp-c-divider);
}

.community-list li:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.community-list a {
  font-weight: 500;
  color: var(--vp-c-brand-1);
  text-decoration: none;
}

.community-list a:hover {
  text-decoration: underline;
}

.community-list span {
  font-size: 0.875rem;
  color: var(--vp-c-text-2);
  line-height: 1.5;
}

.community-badge {
  display: inline-block;
  align-self: flex-start;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  border: 1px solid var(--vp-c-warning-1);
  color: var(--vp-c-warning-1);
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.community-cta {
  display: inline-block;
  align-self: flex-start;
  margin-top: auto;
  padding: 0.55rem 0.9rem;
  border-radius: 8px;
  background-color: var(--vp-c-brand-1);
  color: var(--vp-c-white);
  font-size: 0.9rem;
  font-weight: 500;
  text-decoration: none;
  transition: background-color 0.2s;
}

.community-cta:hover {
  background-color: var(--vp-c-brand-2);
}

.community-cta.secondary {
  background-color: transparent;
  border: 1px solid var(--vp-c-divider);
  color: var(--vp-c-text-1);
}

.community-cta.secondary:hover {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}

.community-cta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1rem;
}

.community-cta-row .community-cta {
  margin-top: 0;
}
</style>
