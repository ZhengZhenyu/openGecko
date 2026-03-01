import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { useFeaturesStore } from './stores/features'

async function init() {
  const app = createApp(App)
  const pinia = createPinia()

  app.use(pinia)
  app.use(router)
  app.use(ElementPlus)

  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  // mount 前拉取功能开关，确保 App.vue 渲染时 store 状态已就绪
  await useFeaturesStore().fetchFeatures()

  app.mount('#app')
}

init()
