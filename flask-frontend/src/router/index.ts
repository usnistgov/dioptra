import { createRouter, createWebHistory } from 'vue-router';
import { LoginCallback } from '@okta/okta-vue'
import HomeView from '../views/HomeView.vue';
import ApiView from '../views/ApiView.vue';
import OktaView from '../views/OktaView.vue';


const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/api',
      name: 'api',
      component: ApiView
    },
    {
      path: '/okta',
      name: 'okta',
      component: OktaView
    },
    { 
      path: '/login/callback', 
      component: LoginCallback 
    },
  ]
});

export default router;
