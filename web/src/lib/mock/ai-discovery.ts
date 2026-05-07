import type { AIDiscoveryData } from "@/lib/types/ai-discovery";

export const aiDiscoveryData: AIDiscoveryData = {
  orgConfig: {
    domains: ["财经", "民生"],
    style: ["客观", "严谨", "深度"],
  },
  totalClues: 12408,
  lastUpdated: "10分钟前",
  clueIds: ["mock-clue-1", "mock-clue-2", "mock-clue-3"],
  recommendations: [
    {
      id: "rec1",
      source: "新浪财经",
      sourceIcon: "newspaper",
      tag: "今日热点 Top 1",
      title: "全球供应链重组：多家科技巨头调整亚洲工厂布局对国内制造业的深远影响",
      reason: "符合财经与深度调性，事件处于发酵初期，涉及国民经济命脉",
      angles: [
        "采访珠三角配套商，探讨\"订单外溢\"后的转型阵痛与机遇",
        "引用近三年海关出口数据，量化分析高新产业韧性",
      ],
    },
    {
      id: "rec2",
      source: "抖音热门",
      sourceIcon: "flame",
      tag: "民生热点",
      title: "预制菜进校园争议：多地家长自发组织送饭，校园餐配监管盲区何在？",
      reason: "触达民生核心关注点，社交平台热度飙升，具冲突感与服务性",
      angles: [
        "走访学校周边配餐工厂，揭露生产环境与食材溯源",
        "对话法律专家，探讨校园餐配招标公开透明度",
      ],
    },
    {
      id: "rec3",
      source: "财新网",
      sourceIcon: "trending-up",
      tag: "深度财经",
      title: "房贷利率二次下调：一线城市楼市回暖信号释放，购房者观望情绪是否松动？",
      reason: "强关联财经板块，政策落地后首周反馈是读者核心痛点",
      angles: [
        "对比利率下调前后，中介平台咨询量与成交转化率",
        "采访刚需型与改善型购房者，还原心理博弈",
      ],
    },
  ],
  totalRecommendations: 24,
};
