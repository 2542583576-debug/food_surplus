import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { title: '登录' } },
  {
    path: '/',
    component: () => import('../layout/AdminLayout.vue'),
    redirect: '/bags',
    children: [
      { path: 'bags', name: 'Bags', component: () => import('../views/Bags.vue'), meta: { title: '魔法袋广场', icon: 'Shop', public: true } },
      { path: 'my-orders', name: 'MyOrders', component: () => import('../views/MyOrders.vue'), meta: { title: '我的订单', icon: 'List', public: true } },
      { path: 'stores', name: 'Stores', component: () => import('../views/Stores.vue'), meta: { title: '自提门店', icon: 'Location', public: true } },
      { path: 'carbon', name: 'Carbon', component: () => import('../views/Carbon.vue'), meta: { title: '环保账本', icon: 'Sunny', public: true } },
      { path: 'bag-admin', name: 'BagAdmin', component: () => import('../views/BagAdmin.vue'), meta: { title: '魔法袋管理', icon: 'Present', merchant: true } },
      { path: 'orders', name: 'Orders', component: () => import('../views/Orders.vue'), meta: { title: '门店订单', icon: 'Tickets', merchant: true } },
      { path: 'categories', name: 'Categories', component: () => import('../views/Categories.vue'), meta: { title: '分类管理', icon: 'Grid', merchant: true } },
      { path: 'products', name: 'Products', component: () => import('../views/Products.vue'), meta: { title: '商品管理', icon: 'Goods', merchant: true } },
      { path: 'blind-boxes', name: 'BlindBoxes', component: () => import('../views/BlindBoxes.vue'), meta: { title: '盲盒管理', icon: 'Box', merchant: true } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || ''} - 惜食魔法袋`
  const store = useUserStore()
  if (to.path !== '/login' && !store.token) {
    return '/login'
  }
  if (to.path === '/login' && store.token) {
    return '/'
  }
  if (to.meta.merchant && store.info && store.info.role !== 1) {
    return '/bags'
  }
})

export default router
