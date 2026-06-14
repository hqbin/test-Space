import { ref } from 'vue'
import axios from 'axios'

const API_BASE_URL = '/api/behavior-tracker'

const EXCLUDED_PAGES = [
  '/testplans/:id/execution',
  '/testplans/:planId/testcases/:testcaseId'
]

function shouldTrackPage(path) {
  return !EXCLUDED_PAGES.some(excluded => {
    const regex = new RegExp('^' + excluded.replace(/:[^/]+/g, '[^/]+') + '$')
    return regex.test(path)
  })
}

async function trackEvent(data) {
  try {
    const token = localStorage.getItem('token')
    await axios.post(API_BASE_URL + '/track', data, {
      timeout: 5000,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      }
    })
  } catch (error) {
    console.warn('Behavior tracking failed:', error)
  }
}

export function useBehaviorTracker() {
  const trackPageView = (pagePath, pageName) => {
    if (!shouldTrackPage(pagePath)) {
      return
    }

    trackEvent({
      behavior_type: 'page_view',
      page_path: pagePath,
      page_name: pageName
    })
  }

  const trackClick = (pagePath, pageName, elementId, elementName) => {
    if (!shouldTrackPage(pagePath)) {
      return
    }

    trackEvent({
      behavior_type: 'click',
      page_path: pagePath,
      page_name: pageName,
      element_id: elementId,
      element_name: elementName
    })
  }

  const trackAction = (pagePath, pageName, actionName, actionType, extraData = null) => {
    if (!shouldTrackPage(pagePath)) {
      return
    }

    trackEvent({
      behavior_type: 'action',
      page_path: pagePath,
      page_name: pageName,
      action_name: actionName,
      action_type: actionType,
      extra_data: extraData ? JSON.stringify(extraData) : null
    })
  }

  return {
    trackPageView,
    trackClick,
    trackAction
  }
}

export function initPageTracking(router, getPageName) {
  router.afterEach((to) => {
    const { trackPageView } = useBehaviorTracker()
    const pageName = getPageName ? getPageName(to) : to.meta.title || to.name || to.path
    trackPageView(to.path, pageName)
  })
}