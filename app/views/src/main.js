import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import vuetify from './plugins/vuetify'
import Axios from 'axios'
import utils from './utils'
import qs from 'querystring'
import LoadingOverlay from './components/LoadingOverlay.vue'

Vue.config.productionTip = false
Axios.defaults.baseURL = '/api'
Axios.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded'
Vue.prototype.$axios = Axios
Vue.prototype.$qs = qs
Vue.use(utils)
Vue.component('v-loading-overlay', LoadingOverlay)

router.beforeEach((to, from, next) => {
  if (to.query.redirect === true && from.meta.type !== 'login') {
    store.commit('setRedirect', from.path)
  }
  if (from.meta.stalling && store.state.stall && to.path !== from.path) {
    const check = window.confirm('表单尚未提交，确定离开?')
    if (!check) {
      return next(false)
    }
  }
  next()
})

window.onbeforeunload = function () {
  if (router.currentRoute.meta.stalling && store.state.stall) {
    return ''
  }
}

new Vue({
  router,
  store,
  vuetify,
  render: h => h(App)
}).$mount('#app')
