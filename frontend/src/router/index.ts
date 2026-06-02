import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/Register.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      component: () => import('@/layouts/DefaultLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
        },
        {
          path: 'hosts',
          name: 'Hosts',
          component: () => import('@/views/Hosts.vue'),
        },
        {
          path: 'scans',
          name: 'Scans',
          component: () => import('@/views/Scans.vue'),
        },
        {
          path: 'collections',
          name: 'Collections',
          component: () => import('@/views/Collections.vue'),
        },
        {
          path: 'platforms',
          name: 'Platforms',
          component: () => import('@/views/Platforms.vue'),
        },
        {
          path: 'applications',
          name: 'Applications',
          component: () => import('@/views/Applications.vue'),
        },
        {
          path: 'applications/:id',
          name: 'ApplicationDetail',
          component: () => import('@/views/ApplicationDetail.vue'),
        },
        {
          path: 'tags',
          name: 'Tags',
          component: () => import('@/views/Tags.vue'),
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('@/views/Settings.vue'),
        },
      ],
    },
  ],
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  
  // If token exists but user is not loaded, try to fetch user info
  if (authStore.token && !authStore.user && !authStore.isLoading) {
    await authStore.fetchCurrentUser()
  }
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login' })
  } else if ((to.name === 'Login' || to.name === 'Register') && authStore.isAuthenticated) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router

