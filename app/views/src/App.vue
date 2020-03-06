<template>
  <v-app>
    <v-app-bar
      app
      color="white"
      style="z-index: 100"
    >
      <v-img
        alt="THU AI"
        class="mx-n4 mb-2 shrink hidden-sm-and-down "
        src="./assets/logo.png"
        contain
        height="48"
        width="174"
        style="cursor: pointer"
        @click="$router.push('/')"
      />
      <div class="mr-4 headline"><b>疫情攻坚战</b></div>

      <v-scroll-x-transition>
        <top-bar v-if="$route.meta.type==='contest'"></top-bar>
      </v-scroll-x-transition>
      <v-spacer></v-spacer>

      <user-bar></user-bar>

    </v-app-bar>

    <v-content>
      <router-view/>
    </v-content>

    <v-footer
      color="#555555"
      dark
    >
      <div>Copyright 2020</div>
    </v-footer>
  </v-app>
</template>

<script>
import TopBar from './components/Topbar.vue'
import UserBar from './components/UserBar.vue'
export default {
  name: 'App',
  components: {
    'top-bar': TopBar,
    'user-bar': UserBar
  },
  created () {
    this.$axios.get('/whoami').then(res => {
      this.$store.commit('login', res.data)
    }).catch(err => {
      if (err.response.state === 400) {
        this.$store.commit('logout')
      }
    })
  },
  beforeDestroy () {
    this.$store.commit('logout')
  }
}
</script>
