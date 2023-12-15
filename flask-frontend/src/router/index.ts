import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import ApiView from '../views/ApiView.vue';
import CodeMirrorView from '../views/CodeMirrorView.vue';
import AceView from '../views/AceView.vue';

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
      path: '/codemirror',
      name: 'codemirror',
      component: CodeMirrorView
    },
    {
      path: '/ace',
      name: 'ace',
      component: AceView
    }
  ]
});

export default router;
