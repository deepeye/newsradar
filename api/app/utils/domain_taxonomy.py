"""Domain taxonomy — classify clues into editorial domain categories."""

# Domain taxonomy: each domain maps to a list of keywords/hashtags
# that signal the clue belongs to that domain.
DOMAIN_TAXONOMY = {
    "政治": ["政治", "反腐", "政府", "政策", "外交", "选举", "立法", "人大",
             "国务院", "党中央", "体制", "民主", "治理", "反腐倡廉"],
    "经济": ["经济", "财经", "金融", "股市", "GDP", "通胀", "货币", "利率",
             "房价", "楼市", "贸易", "关税", "投资", "基金", "债券", "银行",
             "保险", "A股", "港股", "纳斯达克", "供应链", "消费", "就业",
             "失业率", "降息", "加息", "宏观", "微观", "私募"],
    "社会": ["社会", "民生", "疫情", "医疗", "教育", "高考", "养老", "社保",
             "住房", "拆迁", "维权", "安全事故", "灾难", "救援", "慈善",
             "公益", "留守儿童", "农民工", "人口", "生育", "移民", "脱贫",
             "扶贫", "乡村振兴", "城镇化", "社区"],
    "科技": ["科技", "AI", "人工智能", "互联网", "5G", "芯片", "半导体",
             "大数据", "云计算", "区块链", "元宇宙", "自动驾驶", "机器人",
             "数码", "手机", "APP", "算法", "开源", "数字化", "智能",
             "ChatGPT", "deepseek", "量子", "航天", "太空"],
    "评论": ["评论", "观点", "社论", "评论员", "时评", "编者按", "述评",
             "观察", "分析", "解读", "研判"],
    "理论": ["理论", "学术", "研究", "论文", "哲学", "马克思主义",
             "思想家", "学者", "文献", "理论体系", "范式"],
    "体育": ["体育", "足球", "奥运", "NBA", "世界杯", "中超", "CBA",
             "马拉松", "田径", "游泳", "乒乓球", "羽毛球", "网球",
             "拳击", "格斗", "电竞", "亚运", "冬奥", "冠军", "联赛"],
    "文化": ["文化", "娱乐", "电影", "文学", "音乐", "艺术", "书法",
             "戏剧", "综艺", "明星", "偶像", "粉丝", "追星", "非遗",
             "传统文化", "阅读", "出版", "动漫", "游戏"],
    "军事": ["军事", "国防", "武器", "军演", "海军", "空军", "陆军",
             "火箭军", "航母", "战机", "导弹", "军费", "兵役"],
    "国际": ["国际", "全球", "世界", "联合国", "G7", "G20", "APEC",
             "北约", "欧盟", "东盟", "中日", "中美", "中欧", "一带一路",
             "外交", "制裁", "冲突", "战争", "难民"],
}

# Alias mapping: OrgConfig may use alternative domain labels
# e.g. "财经" → "经济", "民生" → "社会"
DOMAIN_ALIASES = {
    "财经": "经济",
    "金融": "经济",
    "民生": "社会",
    "时政": "政治",
    "文艺": "文化",
    "娱乐": "文化",
    "军事安全": "军事",
    "国际关系": "国际",
    "思想": "理论",
}


def resolve_domain(domain: str) -> str:
    """Map an OrgConfig domain label to a taxonomy category."""
    if domain in DOMAIN_TAXONOMY:
        return domain
    return DOMAIN_ALIASES.get(domain, domain)


def classify_domains(title: str, tags: list | None) -> list[str]:
    """Classify a clue into domain categories based on title + tags.

    Returns a list of matched domain names (can be multi-label).
    """
    # Combine all text for keyword matching
    text_parts = [title]
    if tags:
        text_parts.extend(tags)
    combined = " ".join(text_parts)

    matched = []
    for domain, keywords in DOMAIN_TAXONOMY.items():
        for kw in keywords:
            if kw in combined:
                matched.append(domain)
                break  # One keyword match is enough per domain

    return matched