<template>
  <div class="text-center">
    <v-card
      :raised="$vuetify.breakpoint.mdAndUp"
      :outlined="!$vuetify.breakpoint.mdAndUp"
      :width="$vuetify.breakpoint.mdAndUp? '80%' : '100%'"
      style="border: none"
    >
      <v-snackbar top style="margin-top: 60px"  v-model="showErr" color="error" :timeout="3000">
      {{errMessage}}
    </v-snackbar>
      <v-card-title><div class="headline pl-6 pr-6 pb-4 pt-4">登录BotAny</div></v-card-title>
      <v-card-text>
      <div class="title text-center">
                  请从THU AI主网站登录本赛道
                  </div>
          <v-row class="pl-4 pr-4">
            <v-spacer />
            <v-col :cols="12" :sm="6">
              <v-btn
                ref="login"
                color="primary"
                block large
                @click="goToMain"
              >前往主网站
              </v-btn>
            </v-col>
            <v-spacer />
          </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
export default {
  name: 'Login',
  data: () => ({
    handle: '',
    handleRules: [
      v => !!v || '请输入账号',
      v => v.length <= 30 || '输入过长'
    ],
    password: '',
    passwordRules: [
      v => !!v || '请输入密码',
      v => v.length <= 30 || '输入过长'
    ],
    showPassword: false,
    valid: false,
    showErr: false,
    errMessage: '用户不存在或密码错误',
    loading: false
  }),
  methods: {
    switchFocus () {
      this.$refs.password.focus()
    },
    autoSubmit () {
      if (this.$refs.loginForm.validate()) {
        this.login()
      }
    },
    goToMain () {
      window.location = 'https://thu-ai.net'
    },
    login () {
      if (!this.$refs.loginForm.validate()) {
        return
      }
      this.loading = true
      const params = this.$qs.stringify({
        handle: this.handle,
        password: this.password
      })
      this.$axios.post(
        '/login',
        params
      ).then(res => {
        const logindata = {
          id: res.data.id,
          handle: res.data.handle,
          privilege: parseInt(res.data.privilege),
          nickname: res.data.nickname
        }
        this.$store.commit('login', logindata)
        this.loading = false
        if (this.$route.query.redirect) {
          this.$router.push(this.$store.state.redirect)
        } else {
          this.$router.push('/')
        }
      }).catch(() => {
        this.showErr = true
        this.password = ''
        this.loading = false
      })
    }
  }
}
</script>

<style>

</style>
