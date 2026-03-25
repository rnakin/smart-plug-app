import { createApp } from 'vue'
import router from './router/index.js'
import App from './App.vue'
import './assets/global.css'

const app = createApp(App)
app.use(router)
app.mount('#app')
