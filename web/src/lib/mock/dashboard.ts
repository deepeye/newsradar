import type { DashboardData } from "@/lib/types/dashboard";

export const dashboardData: DashboardData = {
  trendingCards: [
    {
      platform: "weibo",
      platformLabel: "微博热搜",
      items: [
        { id: "wb1", rank: 1, title: "全球气候峰会达成最新协议", heatValue: "5,892,341", status: "explosive" },
        { id: "wb2", rank: 2, title: "某一线城市房贷利率再下调", heatValue: "4,215,678", status: "new" },
        { id: "wb3", rank: 3, title: "国产大飞机完成首次跨洋飞行", heatValue: "3,876,543", status: "rank_up" },
        { id: "wb4", rank: 4, title: "春季流感预防指南发布", heatValue: "2,543,210", status: "rank_down" },
        { id: "wb5", rank: 5, title: "大学生特种兵式旅游再走红", heatValue: "2,198,765", status: "rank_up" },
      ],
      lastUpdated: "5分钟前",
    },
    {
      platform: "douyin",
      platformLabel: "抖音热榜",
      items: [
        { id: "dy1", rank: 1, title: "被这组绝美航拍惊艳到了", heatValue: "8,432,109", status: "explosive" },
        { id: "dy2", rank: 2, title: "当南方人第一次看到暴雪", heatValue: "6,543,210", status: "rank_up" },
        { id: "dy3", rank: 3, title: "3分钟速成春季穿搭指南", heatValue: "5,210,987", status: "new" },
        { id: "dy4", rank: 4, title: "给猫咪做的高定小裙子", heatValue: "4,321,098", status: "rank_up" },
        { id: "dy5", rank: 5, title: "全网都在找这位救人英雄", heatValue: "3,987,654", status: "explosive" },
      ],
      lastUpdated: "3分钟前",
    },
    {
      platform: "zhihu",
      platformLabel: "知乎热榜",
      items: [
        { id: "zh1", rank: 1, title: "如何评价最新发布的某款AI？", heatValue: "2,341,000", status: "explosive" },
        { id: "zh2", rank: 2, title: "有哪些让你感叹'知识真有用'？", heatValue: "1,876,543", status: "rank_up" },
        { id: "zh3", rank: 3, title: "普通人如何抓住这一波科技红利？", heatValue: "1,543,210", status: "stable" },
      ],
      lastUpdated: "8分钟前",
    },
    {
      platform: "baidu",
      platformLabel: "百度热搜",
      items: [
        { id: "bd1", rank: 1, title: "2024个人所得税汇算清缴", heatValue: "3,456,789", status: "explosive" },
        { id: "bd2", rank: 2, title: "如何科学应对倒春寒？", heatValue: "2,109,876", status: "rank_up" },
        { id: "bd3", rank: 3, title: "春季赏花地图全攻略", heatValue: "1,876,543", status: "new" },
      ],
      lastUpdated: "2分钟前",
    },
  ],
  kolColumns: [
    {
      platform: "weibo",
      platformLabel: "微博 KOL",
      posts: [
        {
          id: "k1",
          author: "科技微观社 V",
          verified: true,
          content: "手机厂商正在疯狂内卷端侧AI，但真正的杀手级应用还没出现。谁先找到AI手机的使用场景，谁就赢了下半场。",
          likes: 1200,
          shares: 428,
          comments: 156,
          timeAgo: "15分钟前",
        },
        {
          id: "k2",
          author: "财经那些事儿",
          verified: true,
          content: "房贷利率再下调，对家庭资产配置影响几何？刚需购房者迎来窗口期，但改善型需求仍在观望。",
          likes: 856,
          shares: 112,
          comments: 89,
          timeAgo: "1小时前",
        },
      ],
    },
    {
      platform: "twitter",
      platformLabel: "Twitter KOL",
      posts: [
        {
          id: "k3",
          author: "TechCrunch News",
          verified: true,
          content: "SpaceX launches another batch of Starlink satellites, bringing total constellation to over 6,000 units. Global coverage milestone expected by Q3.",
          likes: 15400,
          shares: 2100,
          comments: 432,
          timeAgo: "22分钟前",
        },
        {
          id: "k4",
          author: "Alex Hormozi",
          verified: true,
          content: "Focus on one product, one market, one channel until you hit $1M. Most founders fail by doing too much too soon.",
          likes: 8200,
          shares: 940,
          comments: 210,
          timeAgo: "3小时前",
        },
      ],
    },
    {
      platform: "toutiao",
      platformLabel: "今日头条 KOL",
      posts: [
        {
          id: "k5",
          author: "生活家频道",
          verified: false,
          content: "小户型灯光设计攻略：层高不足2.7m，千万别装吊灯！用轨道射灯加落地灯，空间感瞬间翻倍。",
          likes: 3200,
          shares: 428,
          comments: 328,
          timeAgo: "30分钟前",
        },
        {
          id: "k6",
          author: "历史深度谈",
          verified: true,
          content: "丝绸之路不仅是商路，更是文明对话的走廊。从驼铃到中欧班列，人类对连接的渴望从未改变。",
          likes: 6700,
          shares: 892,
          comments: 892,
          timeAgo: "2小时前",
        },
      ],
    },
  ],
  aiSuggestions: [
    {
      id: "ai1",
      title: "\"赛博养老\"背后的银发经济崛起",
      description: "将微博养老科技话题与知乎讨论的老年人生活质量问题关联，挖掘科技适老化的商业机会与社会需求。",
    },
    {
      id: "ai2",
      title: "春季限定：当非遗遇上旅游特种兵",
      description: "跨平台关联抖音非遗手艺短视频与大学生特种兵旅游趋势，呈现传统文化与年轻消费的碰撞。",
    },
  ],
  activeThreads: 24000,
  topicAlerts: 18,
  quote: {
    text: "权威性来源于数据的密度与筛选的精准度。",
    source: "AI 洞察",
  },
};
