import type { OutlineListResponse } from "@/lib/types/outlines";

export const outlinesData: OutlineListResponse = {
  total: 1,
  items: [
    {
      id: "mock-outline-1",
      title: "2024年全球半导体供应链重组深度分析",
      summary:
        "地缘政治压力持续重塑全球芯片版图，代工势力崛起与制程极限挑战并存。核心冲突为\"国家安全与市场自由流动的博弈\"。投融资环比增长22%，人才缺口达15万人。",
      urgency: "高",
      infoDensity: 92,
      headlines: [
        { id: "h1", style: "硬核新闻风", text: "\"2024半导体蓝皮书：供应链重组下的阵痛与新秩序\"" },
        { id: "h2", style: "叙事分析风", text: "《硅幕重塑：谁在主导这场决定未来的算力竞赛？》" },
        { id: "h3", style: "深度解读风", text: "《从分工到筑墙：透视全球芯片版图的结构性巨变》" },
      ],
      leadParagraph:
        "2024年，地缘经济震荡将半导体产业推向十字路口：美国芯片法案落地两年，产能回流成效初显但矛盾重重；欧洲芯愿景加速推进，汽车半导体优势成为防守壁垒；东南亚以成本红利承接封装测试外溢，但基础设施与人才短板制约升级。当垂直分工开始向区域化闭环转型，全球芯片产业链正经历数十年来最深刻的结构性重构。",
      outlineSections: [
        {
          id: "s1",
          number: "01",
          title: "全球补贴浪潮下的\"产线搬迁记\"",
          items: [
            { id: "s1-1", content: "美国芯片法案两年考：Intel与TSMC亚利桑那州建设进度对比", hasAIRewrite: true },
            { id: "s1-2", content: "欧洲芯愿景：迈向20%全球市场份额，汽车半导体优势防守", hasAIRewrite: true },
          ],
        },
        {
          id: "s2",
          number: "02",
          title: "\"算力饥渴\"下的技术路线分歧",
          items: [
            { id: "s2-1", content: "AI服务器需求暴涨：HBM存储芯片瓶颈，SK海力士与三星竞速", hasAIRewrite: true },
            { id: "s2-2", content: "摩尔定律十字路口：Chiplet与先进封装崛起，封装替代光刻成新引擎", hasAIRewrite: true },
          ],
        },
      ],
      interviewDirections: [
        { id: "i1", role: "政策观察家", description: "布鲁金斯学会分析师，补贴竞赛与产能过剩风险" },
        { id: "i2", role: "一线工厂", description: "亚利桑那州台积电工程师，跨文化管理阻碍" },
        { id: "i3", role: "初创企业", description: "国内GPU独角兽，供应链本土化替代水位" },
      ],
      references: [
        { id: "r1", title: "Gartner 2024 半导体预测报告", source: "Gartner", url: "#" },
        { id: "r2", title: "《经济学人》：算力时代的地理学", source: "经济学人", url: "#" },
        { id: "r3", title: "商务部关于芯片贸易政策的最新简报", source: "商务部", url: "#" },
      ],
      sourceClueIds: ["mock-clue-1", "mock-clue-2"],
      aiModel: "qwen-plus",
      status: "draft",
      createdAt: "2024-01-01T00:00:00Z",
      updatedAt: "2024-01-01T00:00:00Z",
    },
  ],
};
