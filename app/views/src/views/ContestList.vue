<template>
  <div>
    <v-snackbar top style="margin-top: 60px"  v-model="showErr" color="error" :timeout="3000">
      {{errMessage}}
    </v-snackbar>
    <v-container>
      <h2 class="my-4">欢迎来到疫情攻坚战赛道
      </h2>
      <div>当前共有{{total}}场赛事</div>
      <div>
        <v-btn
          text color="primary" class="pa-0"
          v-if="$store.state.privilege === $consts.privilege.organizer"
          :to="`/create`"
        ><v-icon>mdi-plus-box-outline</v-icon>添加一场赛事</v-btn>
      </div>
      <v-row>
        <v-col
          :cols="12" :md="6"
          v-for="(item, index) in contests" :key="index"
        >
          <v-card
            :to="`/contest/${item.id}/main`"
          >
            <v-img :src="$axios.defaults.baseURL + '/contest/' + item.id + '/banner'" :height="180"></v-img>
            <v-card-title>
              <div class="d-inline">{{item.title}}</div>
              <div class="d-inline primary--text ml-2" v-if="item.my_role===$consts.role.moderator">我管理的比赛</div>
              <div class="d-inline primary--text ml-2" v-else-if="item.my_role===$consts.role.imIn">我参加的比赛</div>
            </v-card-title>
            <v-card-subtitle>{{item.time}}</v-card-subtitle>
            <v-card-text>
              <div>{{item.desc}}</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-divider class="my-8" />

      <div>
        <h2>游戏播放器</h2>
        <h3 class="mt-2">效果图</h3>
        <v-row>
          <v-col cols="12" md="6">
            <v-img src="../assets/1.png" />
          </v-col>
          <v-col cols="12" md="6">
            <v-img src="../assets/2.png" />
          </v-col>
          <v-col cols="12" md="6">
            <v-img src="../assets/3.png" />
          </v-col>
          <v-col cols="12" md="6">
            <v-img src="../assets/4.png" />
          </v-col>
        </v-row>

        <h3 class="mt-4 mb-1">下载地址</h3>
        <v-row>
          <v-card target="_blank" outlined class="ma-2 pa-4 text-center" style="font-size: 18px; width: 200px" href="/player/THUAI_v1.3_Windows.zip">
            <div>
              <v-icon large>mdi-microsoft-windows</v-icon>
            </div>
            Windows版
          </v-card>
          <v-card target="_blank" outlined class="ma-2 pa-4 text-center" style="font-size: 18px; width: 200px" href="/player/THUAI_v1.3_Mac.zip">
            <div>
              <v-icon large>mdi-apple</v-icon>
            </div>
            Mac版
          </v-card>
        </v-row>
      </div>

      <v-divider class="my-8" />

      <div>
        <h2>比赛简介</h2>
        <div class="mt-4" style="font-size: 18px; text-indent: 2em;">
          <p>
            人工智能挑战赛（全校本科生编程类赛事）由清华大学多项重要编程类赛事联合而成，在校内拥有广泛的影响力。该赛事由清华大学学生科协主导组织，多个院系学生科协共同主办，旨在鼓励不同水平的同学大胆创新、积极合作、认真实践，做出优秀的作品，在人工智能挑战赛这个平台中，互相交流学习、提升自我。
          </p>
          <p>
大赛面向有编程基础、对人工智能感兴趣的各年级本科生，同时希望为新生体验我校科技赛事、融入校园科创氛围、了解学生科协等提供契机。比赛选用C/C++为参赛语言，以解决指定问题或多AI对战的方式，锻炼同学的编程能力，体验编程的乐趣。
          </p>
          <p>
本届比赛凝聚了清华大学各个院系最优秀的同学组成的开发团队，全力开发出了富有趣味性、挑战性的比赛平台。比赛紧跟时代召唤，参考《中共中央国务院关于全面加强生态环境保护 坚决打好污染防治攻坚战的意见》关于“着力解决大气、水、土壤污染等突出环境问题，持续改善生态环境质量”的有关要求，以环境保卫战为背景，设置了三大“保卫战”为主题的赛题赛道，游戏形式多样，同学们可以根据自身对于赛题赛道和比赛形式的实际兴趣选择参加。
          </p>
        </div>

      </div>
    </v-container>
  </div>
</template>

<script>
export default {
  name: 'ContestList',
  data: () => ({
    total: 0,
    contests: [],
    errMessage: '无法连接服务器，请检查网络',
    showErr: false
  }),
  mounted () {
    this.getContestList()
  },
  methods: {
    getContestList () {
      this.$axios.get('/contest/list').then(res => {
        this.contests = res.data
        this.total = res.data.length
        this.contests.forEach(item => {
          const start = this.$functions.dateTimeString(item.start_time)
          const end = this.$functions.dateTimeString(item.end_time)
          item.time = start + ' TO ' + end
          // console.log(item)
        })
      }).catch(err => {
        if (err.response.state >= 400) {
          this.showErr = true
        }
      })
    }
  }
}
</script>

<style>

</style>
