import { createRouter, createWebHistory } from 'vue-router'
// 懒加载包装函数
const lazyLoad = (importFn) => {
  return () => {
    return importFn().catch((error) => {
      console.error('[Router] Chunk load failed, retrying...', error)
      return new Promise((resolve) => {
        setTimeout(() => {
          importFn().then(resolve).catch((err2) => {
            console.error('[Router] Chunk load retry failed:', err2)
            resolve(importFn())
          })
        }, 1500)
      })
    })
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: lazyLoad(() => import('@/views/HomeView.vue')),
    },
    {
      path: '/articles',
      name: 'articles',
      component: lazyLoad(() => import('@/views/HomeView.vue')),
    },
    {
      path: '/article/:id',
      name: 'article-detail',
      component: lazyLoad(() => import('@/views/ArticleView.vue')),
    },
    {
      path: '/about',
      name: 'about',
      component: lazyLoad(() => import('@/views/AboutView.vue')),
    },
    {
      path: '/search',
      name: 'search',
      component: lazyLoad(() => import('@/views/SearchView.vue')),
    },
    {
      path: '/timeline',
      name: 'timeline',
      component: lazyLoad(() => import('@/views/TimelineView.vue')),
    },
    {
      path: '/categories',
      name: 'categories',
      component: lazyLoad(() => import('@/views/CategoryView.vue')),
    },
    {
      path: '/series',
      name: 'series',
      component: lazyLoad(() => import('@/views/SeriesView.vue')),
    },
    {
      path: '/series/:slug',
      name: 'series-detail',
      component: lazyLoad(() => import('@/views/SeriesDetailView.vue')),
    },
    {
      path: '/archive',
      name: 'archive',
      component: lazyLoad(() => import('@/views/ArchiveView.vue')),
    },
    {
      path: '/archive/:year/:month',
      name: 'archive-month',
      component: lazyLoad(() => import('@/views/ArchiveView.vue')),
    },
    {
      path: '/friends',
      name: 'friends',
      component: lazyLoad(() => import('@/views/FriendLinkView.vue')),
    },
    {
      path: '/notes',
      name: 'notes',
      component: lazyLoad(() => import('@/views/NotesView.vue')),
    },
    {
      path: '/tools',
      name: 'tools',
      component: lazyLoad(() => import('@/views/ToolsView.vue')),
    },
    {
      path: '/monitoring',
      name: 'monitoring',
      component: lazyLoad(() => import('@/views/MonitoringView.vue')),
    },
    {
      path: '/write',
      name: 'write',
      component: lazyLoad(() => import('@/views/GuestEditorView.vue')),
    },
    {
      path: '/login',
      name: 'login',
      component: lazyLoad(() => import('@/views/LoginView.vue')),
      meta: { guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: lazyLoad(() => import('@/views/RegisterView.vue')),
      meta: { guestOnly: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: lazyLoad(() => import('@/views/ProfileView.vue')),
      meta: { requiresAuth: true },
    },
    {
      path: '/editor',
      name: 'editor',
      component: lazyLoad(() => import('@/views/EditorView.vue')),
      meta: { requiresAuth: true },
    },
    {
      path: '/editor/:id',
      name: 'editor-edit',
      component: lazyLoad(() => import('@/views/EditorView.vue')),
      meta: { requiresAuth: true },
    },
    {
      path: '/oauth/callback',
      name: 'oauth-callback',
      component: lazyLoad(() => import('@/views/OAuthCallbackView.vue')),
    },
  ],
})
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    next({
      path: '/login',
      query: { redirect: to.fullPath },
    })
    return
  }
  if (to.meta.guestOnly && token) {
    next('/')
    return
  }
  next()
})

router.onError((error, to) => {
  console.error('[Router] Navigation error to', to.path, ':', error)
})

export default router