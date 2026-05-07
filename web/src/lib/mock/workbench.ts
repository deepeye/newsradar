import type { ArticleResponse, AISuggestion, ContentMetrics, ReferenceDoc } from "@/lib/types/workbench";

const suggestions: AISuggestion[] = [
  {
    id: "sug1",
    type: "style",
    original: "全球半导体产业版图正在经历一场前所未有的重塑",
    suggested: "一场静默的产业地震正在改写全球半导体版图——这不是预言，而是正在发生的事实",
    reason: "建议调整首段为更具紧迫感的商业评论风格，增强读者阅读动力",
  },
  {
    id: "sug2",
    type: "grammar",
    original: "英特尔在此投资70亿美元建设3D封装工厂",
    suggested: "英特尔宣布追加70亿美元投资，用于建设其全球最大的3D Foveros封装工厂",
    reason: "补充修饰语使表述更准确，突出其全球最大规模的战略意义",
  },
];

const metrics: ContentMetrics = {
  objectivity: 88,
  readability: "B2",
};

const references: ReferenceDoc[] = [
  { id: "ref1", title: "2023全球半导体行业年度报告", source: "Gartner", lastUpdated: "2小时前更新" },
  { id: "ref2", title: "东南亚电力基础设施现状简报", source: "国际能源署", lastUpdated: "12月20日" },
];

const content = `全球半导体产业版图正在经历一场前所未有的重塑。在地缘政治压力和"China Plus One"战略推动下，马来西亚、越南和印度正迅速崛起为新的制造高地。

槟城，这座马来西亚北部城市，如今承载着全球约13%的封装测试需求。英特尔在此投资70亿美元建设3D封装工厂，成为其在亚洲最大的先进封装基地。与此同时，越南胡志明市周边的产业园也在加速吸引半导体企业入驻。

然而，东南亚的崛起并非没有挑战。基础设施不足、高技能人才短缺以及电力供应的稳定性，都是制约产业升级的关键因素。

[此处待补充：关于新加坡在高度自动化晶圆厂领域的竞争优势分析...]`;

export const mockArticle: ArticleResponse = {
  id: "mock-article-1",
  outlineId: "mock-outline-1",
  title: "全球半导体供应链重组：东南亚成为新兴制造高地",
  authorId: null,
  content,
  wordCount: 1248,
  targetWordCount: 1600,
  completionPercent: 75,
  urgent: true,
  aiSuggestions: suggestions,
  metrics,
  references,
  status: "draft",
  lastSavedAt: null,
  createdAt: "2024-10-24T08:00:00Z",
  updatedAt: "2024-10-24T08:00:00Z",
};
