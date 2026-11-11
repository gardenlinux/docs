// Plausible analytics wiring for the Garden Linux docs.
// Ported from gardener/documentation (.vitepress/theme/utils/analytics.ts).
// Cookieless: no per-user session chaining, no persistent identifiers, no PII.
import type { Router } from 'vitepress'
import type { track as trackFn } from '@plausible-analytics/tracker'

type Track = typeof trackFn

/** Report client-side 404s so broken links surface in the dashboard. */
function trackNotFound(router: Router, track: Track): void {
  const prev = router.onAfterRouteChanged
  router.onAfterRouteChanged = (to) => {
    if (router.route.data.isNotFound) {
      track('404', { props: { path: to }, interactive: false })
    }
    return prev?.(to)
  }
}

/**
 * Unify page URLs sent to Plausible to the gardener convention (always a trailing slash),
 * so `/docs`, `/docs/`, `/docs.html` and `/docs/index.html` do not split metrics.
 * This site has no cleanUrls, so Netlify serves the same page under `.html` and extensionless paths.
 */
export function normalizeEventUrl(rawUrl: string): string {
  try {
    const parsed = new URL(rawUrl)
    parsed.pathname = parsed.pathname.replace(/(\/index)?\.html$/, '')
    if (!parsed.pathname.endsWith('/') && !/\.[a-z0-9]+$/i.test(parsed.pathname)) {
      parsed.pathname += '/'
    }
    return parsed.toString()
  } catch {
    return rawUrl
  }
}

export function initAnalytics(router: Router): Promise<void> {
  // Return the promise so enhanceApp can await it before VitePress runs the
  // initial navigation; otherwise the 404 hook can be installed too late to
  // catch a direct hit on a non-existent route.
  return import('@plausible-analytics/tracker').then(({ init, track }) => {
    init({
      domain: 'docs.gardenlinux.org',
      // Netlify proxy (netlify.toml) avoids adblockers; localhost is ignored by the tracker (captureOnLocalhost defaults to false)
      endpoint: '/pa/event',
      autoCapturePageviews: true,
      outboundLinks: true,
      transformRequest: (payload) => ({
        ...payload,
        u: normalizeEventUrl(payload.u),
      }),
    })
    trackNotFound(router, track)
  })
}
