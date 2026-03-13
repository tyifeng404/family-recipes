"""
builtin_recipes.py —— 系统内置经典菜谱库

- 中餐经典：约 100 道
- 外国菜：50 道（西餐/日本菜/朝鲜菜/东南亚菜/其他地区，各 10 道）
- 仅保留核心主料，忽略常见调料和佐料
- 每道菜提供 3~5 条制作要点
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from cuisine import (
    DEFAULT_DIFFICULTY,
    FOREIGN_CUISINE_OPTIONS,
)

BUILTIN_RECIPE_VERSION = "2026-03-13-rich-v2"
PHOTO_DIR = Path(__file__).resolve().parent / "assets" / "recipe_photos"


def _number_points(points: list[str]) -> list[str]:
    return [f"{i}. {text}" for i, text in enumerate(points, 1)]


def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


POINT_TEMPLATES: dict[str, list[str]] = {
    "stir_fry": [
        "食材切配大小尽量一致，保证受热均匀。",
        "按先肉后菜或先硬后软顺序下锅。",
        "全程中大火快炒，避免出水影响口感。",
        "临出锅前快速翻匀，保持脆嫩。",
    ],
    "braise": [
        "主料先处理至表面定型，再进入焖煮阶段。",
        "加液体后保持小火，让食材慢慢入味。",
        "中途观察汤汁浓度，避免糊底。",
        "最后收汁到挂勺状态再出锅。",
    ],
    "stew": [
        "食材块度适中，确保成熟时间接近。",
        "先处理肉类腥味，再与蔬菜同炖。",
        "小火慢炖比大火快煮更易出香。",
        "软烂度达到后再调整浓稠度。",
    ],
    "steam": [
        "主料摆放平整，尽量厚薄一致。",
        "蒸锅必须上汽后再入锅计时。",
        "控制蒸制时长，避免过老或过生。",
    ],
    "deep_fry": [
        "食材表面水分擦干再下锅，减少溅油。",
        "分次下锅保持油温稳定。",
        "需要酥脆口感时可复炸 1 次。",
        "炸后及时沥油，避免回软。",
    ],
    "boil": [
        "提前规划下锅顺序，先熟后熟分开控制。",
        "保持微沸状态，口感更稳定。",
        "食材刚熟即离火，避免煮老。",
    ],
    "soup": [
        "主料先做基础处理，汤底更干净。",
        "先大火煮开再小火慢熬。",
        "以食材本味为主，避免过度复合。",
        "出锅前补充易熟食材保持口感。",
    ],
    "porridge": [
        "米提前浸泡可缩短熬制时间。",
        "先把米煮开花，再加入主料。",
        "保持小火并适当搅动防粘底。",
        "浓稠度达到个人喜好时出锅。",
    ],
    "fried_rice": [
        "优先使用隔夜饭，颗粒更分明。",
        "先炒香主料再入米饭，层次更清晰。",
        "持续翻散米饭，避免结团。",
        "米粒均匀裹香后即可出锅。",
    ],
    "noodle": [
        "面条和浇头并行准备提高效率。",
        "面条煮到略有弹性即可捞出。",
        "浇头和面条结合后快速拌匀。",
    ],
    "dumpling": [
        "馅料含水量适中，避免破皮。",
        "封口要压实，防止煮时开裂。",
        "下锅后轻推防粘底，浮起后再煮一会。",
    ],
    "bun": [
        "面团发酵到位决定松软度。",
        "包制时收口要紧，避免漏馅。",
        "二次醒发后再蒸，体积更饱满。",
    ],
    "pancake": [
        "面团静置后再擀制更易成型。",
        "锅温稳定是形成层次的关键。",
        "两面烙至金黄即可，避免过干。",
    ],
    "cold": [
        "主料汆熟后要快速冷却。",
        "切配粗细一致，口感更统一。",
        "拌匀后静置片刻再食用。",
    ],
    "roast": [
        "主料表面尽量擦干再烤制。",
        "中途可翻面一次，受热更均匀。",
        "达到目标上色后静置再切。",
    ],
    "salad": [
        "蔬菜控干水分避免出水。",
        "先混合耐拌食材，再加入脆嫩食材。",
        "食用前再拌合，口感更新鲜。",
    ],
    "pasta": [
        "意面煮到略硬芯口感最佳。",
        "酱汁提前准备好，避免意面久放。",
        "意面与酱汁同锅拌匀更入味。",
    ],
    "pizza": [
        "面饼厚薄尽量均匀。",
        "主料不要过量，避免饼底潮湿。",
        "高温短时烘烤更容易形成焦香。",
    ],
    "risotto": [
        "米要分次吸收液体，不要一次加满。",
        "持续搅动帮助释放淀粉形成奶感。",
        "收尾时保留流动性，不要煮成干饭。",
    ],
    "bake": [
        "烤盘厚薄和摆放会影响受热。",
        "提前预热可减少熟度偏差。",
        "表面上色后可加盖防过焦。",
        "出炉静置后再切分更完整。",
    ],
    "sandwich": [
        "主料和面包尺寸尽量匹配。",
        "含水食材要提前沥干。",
        "切分前轻压定型，层次更整齐。",
    ],
    "roll": [
        "内馅提前处理成熟并控干水分。",
        "卷制时从紧到松，保持形状稳定。",
        "切段前先静置定型，切口更整齐。",
    ],
    "grill": [
        "食材厚度控制一致。",
        "先高温上色再补熟中心。",
        "出锅后静置 2~3 分钟再切。",
    ],
    "dessert": [
        "原料比例要尽量准确。",
        "混合时避免过度搅打影响结构。",
        "冷却或定型完成后再切分。",
    ],
}


DETAIL_TEMPLATES: dict[str, list[str]] = {
    "stir_fry": [
        "将主要食材分别改刀，硬质食材切薄片、叶菜切段备用。",
        "肉类或海鲜先做基础腌制，静置 10 分钟后沥干多余水分。",
        "热锅热油先下耐炒食材，再下易熟食材，中大火连续翻炒。",
        "根据成熟度分次调味，翻匀后观察锅内水分及时收干。",
        "出锅前快速复炒 10 秒，保持食材脆嫩与香气。",
    ],
    "braise": [
        "主料切块并做好预处理，表面尽量控干水分。",
        "锅中少油将主料煸炒至微黄，激发香气和焦香层次。",
        "加入液体至刚好没过食材，小火慢焖使其充分入味。",
        "中途检查软烂度和汤汁浓度，必要时少量补水。",
        "最后开中火收汁到挂勺状态，装盘即可。",
    ],
    "stew": [
        "将主料和配料切成大小接近的块状，保证成熟时间一致。",
        "肉类先焯水或煎封，蔬菜类食材单独备用。",
        "加足量液体后先煮开，再转小火慢炖 30~60 分钟。",
        "中途轻轻翻动并观察软烂度，避免糊底或过度破碎。",
        "达到软烂浓郁后调整口感，盛出即可。",
    ],
    "steam": [
        "主料洗净改刀后平铺摆盘，厚薄尽量一致。",
        "蒸锅提前烧开，上汽后再放入食材开始计时。",
        "按食材厚薄控制蒸制时长，期间尽量少开盖。",
        "蒸熟后焖 1 分钟再开盖，避免温差导致口感变差。",
        "取出后按经典方式完成收尾即可上桌。",
    ],
    "deep_fry": [
        "主料控干水分并完成裹粉或挂糊处理。",
        "油温升至约 160~170°C 分批下锅，避免骤降。",
        "炸至定型后捞出沥油，必要时静置片刻。",
        "将油温升至 180°C 复炸 10~30 秒提升酥脆度。",
        "快速调味或淋汁后立即装盘。",
    ],
    "boil": [
        "主料和配料分别切配，按耐煮程度分组。",
        "水或汤底煮开后先下耐煮食材，再下易熟食材。",
        "保持微沸状态，避免大滚导致口感变老。",
        "按经典熟度标准捞出或连汤盛碗。",
        "最后补充点缀配料即可食用。",
    ],
    "soup": [
        "主料处理干净并改刀，汤底食材单独准备。",
        "先将汤底煮开，再放入主料小火慢熬出鲜味。",
        "根据食材特性分段加入配料，避免同熟度冲突。",
        "全程保持小火，必要时撇去浮沫保持清爽。",
        "出锅前补充易熟食材并调整口感后盛碗。",
    ],
    "porridge": [
        "米提前浸泡并冲洗，主料切小丁备用。",
        "米与水先煮至开花，再加入主料继续熬煮。",
        "中小火保持轻微翻滚，间隔搅动防粘底。",
        "粥体逐渐浓稠后再加入易熟配料。",
        "达到顺滑稠度后即可出锅。",
    ],
    "fried_rice": [
        "主料切丁，米饭提前打散避免结块。",
        "先炒香鸡蛋或肉类，再加入配菜翻炒断生。",
        "倒入米饭后持续翻散，确保受热均匀。",
        "按经典口感补充调味并炒至粒粒分明。",
        "起锅前大火快炒 10 秒提升锅气。",
    ],
    "noodle": [
        "主料切配并并行准备浇头或汤底。",
        "面条煮至 8~9 成熟后捞出控水。",
        "将面条与浇头或汤底组合，确保比例平衡。",
        "快速翻拌或回煮 30 秒使味道融合。",
        "装碗后补充经典点缀即可。",
    ],
    "dumpling": [
        "主料切碎后拌成馅料，控制含水量。",
        "面皮包入适量馅料并压实封口。",
        "水开后下锅，轻推防止粘连。",
        "浮起后继续煮至馅心完全熟透。",
        "捞出沥水后即可上桌。",
    ],
    "bun": [
        "完成面团一发并准备好馅料。",
        "面团排气分剂，擀成中间厚边缘薄。",
        "包入馅料收口，摆入蒸屉进行二发。",
        "水开上汽后蒸制到位，关火焖 2 分钟。",
        "开盖取出即可食用。",
    ],
    "pancake": [
        "将面团或面糊静置后分份处理。",
        "平底锅预热后少油，放入饼坯整形。",
        "中小火慢烙，适时翻面保证受热均匀。",
        "烙至两面金黄并熟透后出锅。",
        "切块后按经典吃法搭配即可。",
    ],
    "cold": [
        "主料先汆熟或煮熟，随后快速降温。",
        "按食材特性切片或切丝，保持大小一致。",
        "与辅料充分拌匀后静置 5 分钟入味。",
        "装盘时注意层次和摆放整洁。",
        "食用前可再次轻拌确保味道均匀。",
    ],
    "roast": [
        "主料完成预处理并擦干表面水分。",
        "烤箱预热后放入主料，按厚度设置时间。",
        "中途翻面或转向，确保上色均匀。",
        "达到目标熟度后取出静置回汁。",
        "切配装盘并搭配经典配菜。",
    ],
    "salad": [
        "蔬菜类食材洗净控水，蛋白质食材提前处理。",
        "先混合耐拌食材，再加入叶菜类食材。",
        "按经典比例加入调味并轻柔翻拌。",
        "检查口感平衡后立即装盘。",
        "食用前可按需补充脆感配料。",
    ],
    "pasta": [
        "锅中加水煮沸后下意面，煮至略有硬芯。",
        "并行处理酱汁主料，炒至香气充分释放。",
        "将意面与酱汁同锅拌煮 1 分钟融合风味。",
        "根据浓稠度少量补加面汤调整口感。",
        "装盘后撒上经典配料即可。",
    ],
    "pizza": [
        "面饼擀平后静置回弹，准备好配料。",
        "在面饼上按顺序铺底酱、主料和奶酪。",
        "预热烤箱后高温烘烤至边缘上色。",
        "观察饼底熟度，必要时延长 1~2 分钟。",
        "出炉后稍冷却切块食用。",
    ],
    "risotto": [
        "主料切丁并预热高汤保持温热。",
        "将米与主料翻炒后分次加入高汤。",
        "每次吸收后再补加，持续搅动释放淀粉。",
        "煮至米芯微弹并呈奶油质地。",
        "关火后静置 1 分钟再装盘。",
    ],
    "bake": [
        "主料处理后均匀铺入烤盘。",
        "按层次加入辅料并做好表面整理。",
        "预热后入炉烘烤，中途观察上色情况。",
        "达到熟度后取出静置，防止切分散开。",
        "切块装盘并按经典方式搭配。",
    ],
    "sandwich": [
        "主料先处理成熟并切成适口尺寸。",
        "面包轻微加热，提升香气和支撑力。",
        "按经典层次放置主料和蔬菜。",
        "轻压定型后对切，保证断面整齐。",
        "立即食用可获得最佳口感。",
    ],
    "roll": [
        "主料提前处理成熟并充分控水。",
        "将饼皮或米纸铺平，放入配料并整理形状。",
        "按由内向外方式卷紧，保持结构稳定。",
        "静置 1~2 分钟后切段装盘。",
        "搭配经典蘸料即可食用。",
    ],
    "grill": [
        "主料表面擦干并按厚度均匀处理。",
        "烤盘或烤架预热后放入主料煎烤。",
        "根据厚度翻面并控制中心熟度。",
        "达到目标上色后离火静置回汁。",
        "切配后搭配配菜上桌。",
    ],
    "dessert": [
        "按比例准备原料并完成基础混合。",
        "将混合物倒入模具并抹平表面。",
        "根据配方烘烤或冷藏至定型。",
        "取出后冷却到适宜切分温度。",
        "完成装饰后即可食用。",
    ],
}


FULL_INGREDIENT_BASE = {
    "中餐": ["食用油", "盐", "生抽", "料酒", "姜", "蒜"],
    "西餐": ["橄榄油", "盐", "黑胡椒"],
    "日本菜": ["酱油", "味醂", "清酒", "盐"],
    "朝鲜菜": ["韩式辣酱", "蒜", "芝麻油", "糖"],
    "东南亚菜": ["鱼露", "青柠", "糖", "蒜"],
    "其他地区": ["橄榄油", "盐", "黑胡椒", "蒜"],
}


TECHNIQUE_EXTRAS = {
    "deep_fry": ["淀粉"],
    "braise": ["冰糖"],
    "stew": ["洋葱"],
    "soup": ["清水"],
    "pasta": ["帕玛森奶酪"],
    "pizza": ["奶酪"],
    "risotto": ["高汤"],
    "dessert": ["糖"],
}


def _hash_name(name: str) -> str:
    return hashlib.md5(name.encode("utf-8")).hexdigest()[:16]


def _photo_relpath(name: str) -> str:
    return f"assets/recipe_photos/{_hash_name(name)}.svg"


def _create_photo_svg(name: str, cuisine_group: str, cuisine: str, relpath: str):
    path = Path(__file__).resolve().parent / relpath
    if path.exists():
        return
    subtitle = f"{cuisine_group} / {cuisine}"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760">
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#fff8e1"/>
    <stop offset="100%" stop-color="#ffe0b2"/>
  </linearGradient>
</defs>
<rect width="1200" height="760" fill="url(#g)"/>
<rect x="60" y="60" width="1080" height="640" rx="28" fill="#ffffff" opacity="0.82"/>
<text x="600" y="310" text-anchor="middle" fill="#4e342e" font-size="78" font-family="Noto Sans SC, PingFang SC, sans-serif">{name}</text>
<text x="600" y="390" text-anchor="middle" fill="#6d4c41" font-size="36" font-family="Noto Sans SC, PingFang SC, sans-serif">{subtitle} · 经典做法配图</text>
<text x="600" y="590" text-anchor="middle" fill="#8d6e63" font-size="28" font-family="Noto Sans SC, PingFang SC, sans-serif">可在 assets/recipe_photos 中替换为真实菜品照片</text>
</svg>
"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg, encoding="utf-8")
    except OSError:
        # 兼容只读部署环境：无法写入时保留 photo 路径，页面会提示文件缺失。
        return


def _build_all_ingredients(
    main_ingredients: list[str],
    cuisine_group: str,
    cuisine: str,
    technique: str,
) -> list[str]:
    if cuisine_group == "中餐":
        base = FULL_INGREDIENT_BASE["中餐"]
    else:
        base = FULL_INGREDIENT_BASE.get(cuisine, FULL_INGREDIENT_BASE["其他地区"])
    extras = TECHNIQUE_EXTRAS.get(technique, [])
    return _dedup(list(main_ingredients) + base + extras)


def _build_detailed_steps(
    name: str,
    technique: str,
    main_ingredients: list[str],
) -> list[str]:
    templates = DETAIL_TEMPLATES.get(technique, DETAIL_TEMPLATES["stir_fry"])
    lead = "、".join(main_ingredients[:3]) if main_ingredients else "主料"
    customized = [f"【{name}】{templates[0].replace('主料', lead, 1)}"]
    customized.extend(templates[1:])
    return _number_points(customized)


def _build_entry(
    name: str,
    ingredients: list[str],
    technique: str,
    cuisine_group: str,
    cuisine: str,
    tags: list[str] | None = None,
    difficulty: str = DEFAULT_DIFFICULTY,
) -> dict:
    tips = POINT_TEMPLATES.get(technique, POINT_TEMPLATES["stir_fry"])
    detailed_steps = _build_detailed_steps(name, technique, ingredients)
    all_ingredients = _build_all_ingredients(ingredients, cuisine_group, cuisine, technique)
    photo = _photo_relpath(name)
    _create_photo_svg(name, cuisine_group, cuisine, photo)
    return {
        "steps": detailed_steps,
        "tips": _number_points(tips),
        "ingredients": ingredients,
        "all_ingredients": all_ingredients,
        "photo": photo,
        "cuisine_group": cuisine_group,
        "cuisine": cuisine,
        "tags": tags or [],
        "difficulty": difficulty,
        "owner": "system",
        "is_builtin": True,
        "builtin_version": BUILTIN_RECIPE_VERSION,
    }


CHINESE_CLASSICS: list[tuple[str, list[str], str]] = [
    ("麻婆豆腐", ["北豆腐", "牛肉末", "蒜苗"], "braise"),
    ("宫保鸡丁", ["鸡腿肉", "花生米", "黄瓜"], "stir_fry"),
    ("鱼香肉丝", ["猪里脊", "木耳", "胡萝卜"], "stir_fry"),
    ("回锅肉", ["五花肉", "青蒜", "豆干"], "stir_fry"),
    ("青椒肉丝", ["猪里脊", "青椒", "木耳"], "stir_fry"),
    ("京酱肉丝", ["猪里脊", "大葱", "豆皮"], "stir_fry"),
    ("糖醋里脊", ["猪里脊", "鸡蛋", "淀粉"], "deep_fry"),
    ("锅包肉", ["猪里脊", "胡萝卜", "香菜"], "deep_fry"),
    ("水煮肉片", ["猪里脊", "豆芽", "莴笋"], "boil"),
    ("水煮鱼", ["草鱼", "豆芽", "莴笋"], "boil"),
    ("酸菜鱼", ["黑鱼", "酸菜", "豆芽"], "boil"),
    ("夫妻肺片", ["牛肉", "牛肚", "芹菜"], "cold"),
    ("口水鸡", ["鸡腿", "黄瓜", "花生碎"], "cold"),
    ("辣子鸡", ["鸡腿肉", "干辣椒", "花椒"], "deep_fry"),
    ("白切鸡", ["三黄鸡", "葱", "姜"], "boil"),
    ("豉油鸡", ["鸡腿", "葱", "姜"], "braise"),
    ("盐焗鸡", ["鸡", "姜", "粗盐"], "roast"),
    ("啤酒鸭", ["鸭肉", "啤酒", "青椒"], "braise"),
    ("北京烤鸭", ["鸭", "黄瓜", "薄饼"], "roast"),
    ("酱爆鸭丁", ["鸭胸肉", "黄瓜", "花生米"], "stir_fry"),
    ("红烧肉", ["五花肉", "姜", "葱"], "braise"),
    ("梅菜扣肉", ["五花肉", "梅干菜", "姜"], "steam"),
    ("东坡肉", ["五花肉", "葱", "姜"], "braise"),
    ("粉蒸肉", ["五花肉", "蒸肉米粉", "南瓜"], "steam"),
    ("木须肉", ["猪里脊", "鸡蛋", "黄瓜"], "stir_fry"),
    ("蒜泥白肉", ["五花肉", "黄瓜", "蒜"], "cold"),
    ("小炒黄牛肉", ["牛里脊", "小米椒", "香菜"], "stir_fry"),
    ("孜然羊肉", ["羊肉", "洋葱", "香菜"], "stir_fry"),
    ("葱爆羊肉", ["羊肉片", "大葱", "洋葱"], "stir_fry"),
    ("红烧排骨", ["猪排骨", "土豆", "胡萝卜"], "braise"),
    ("糖醋排骨", ["猪排骨", "芝麻", "葱"], "braise"),
    ("可乐鸡翅", ["鸡翅", "可乐", "姜"], "braise"),
    ("小鸡炖蘑菇", ["鸡块", "榛蘑", "粉条"], "stew"),
    ("东北乱炖", ["土豆", "茄子", "豆角"], "stew"),
    ("猪肉炖粉条", ["五花肉", "粉条", "白菜"], "stew"),
    ("土豆炖牛肉", ["牛腩", "土豆", "胡萝卜"], "stew"),
    ("番茄牛腩煲", ["牛腩", "番茄", "洋葱"], "stew"),
    ("萝卜牛腩煲", ["牛腩", "白萝卜", "胡萝卜"], "stew"),
    ("黄焖鸡", ["鸡腿", "香菇", "土豆"], "braise"),
    ("三杯鸡", ["鸡腿肉", "九层塔", "蒜"], "braise"),
    ("香菇滑鸡", ["鸡腿肉", "香菇", "木耳"], "stir_fry"),
    ("咖喱鸡块", ["鸡腿肉", "土豆", "胡萝卜"], "stew"),
    ("韭菜炒鸡蛋", ["韭菜", "鸡蛋", "蒜"], "stir_fry"),
    ("韭黄炒肉丝", ["韭黄", "猪里脊", "木耳"], "stir_fry"),
    ("蒜苔炒肉", ["蒜苔", "猪肉", "胡萝卜"], "stir_fry"),
    ("芹菜炒牛肉", ["芹菜", "牛里脊", "红椒"], "stir_fry"),
    ("荷兰豆炒腊肠", ["荷兰豆", "腊肠", "蒜"], "stir_fry"),
    ("西红柿炒鸡蛋", ["番茄", "鸡蛋", "葱"], "stir_fry"),
    ("干煸豆角", ["四季豆", "猪肉末", "蒜"], "stir_fry"),
    ("手撕包菜", ["卷心菜", "蒜", "干辣椒"], "stir_fry"),
    ("鱼香茄子", ["茄子", "猪肉末", "青椒"], "braise"),
    ("红烧茄子", ["茄子", "青椒", "蒜"], "braise"),
    ("地三鲜", ["土豆", "茄子", "青椒"], "deep_fry"),
    ("干锅花菜", ["花菜", "五花肉", "青椒"], "stir_fry"),
    ("酸辣土豆丝", ["土豆", "胡萝卜", "青椒"], "stir_fry"),
    ("虎皮青椒", ["青椒", "蒜", "肉末"], "stir_fry"),
    ("家常豆腐", ["北豆腐", "木耳", "青椒"], "stir_fry"),
    ("白菜炖豆腐", ["大白菜", "北豆腐", "粉丝"], "stew"),
    ("上汤娃娃菜", ["娃娃菜", "皮蛋", "咸蛋"], "boil"),
    ("蚝油生菜", ["生菜", "蒜", "香菇"], "boil"),
    ("清蒸鲈鱼", ["鲈鱼", "葱", "姜"], "steam"),
    ("红烧鲫鱼", ["鲫鱼", "姜", "葱"], "braise"),
    ("松鼠桂鱼", ["桂鱼", "豌豆", "胡萝卜"], "deep_fry"),
    ("剁椒鱼头", ["鱼头", "剁椒", "葱"], "steam"),
    ("白灼虾", ["虾", "姜", "葱"], "boil"),
    ("油焖大虾", ["大虾", "姜", "蒜"], "braise"),
    ("干烧大虾", ["大虾", "姜", "蒜"], "braise"),
    ("宫保虾球", ["虾仁", "花生米", "黄瓜"], "stir_fry"),
    ("椒盐虾", ["虾", "蒜", "洋葱"], "deep_fry"),
    ("葱姜炒蟹", ["梭子蟹", "葱", "姜"], "stir_fry"),
    ("香煎带鱼", ["带鱼", "姜", "葱"], "deep_fry"),
    ("糖醋鱼块", ["鱼块", "菠萝", "青椒"], "deep_fry"),
    ("冬瓜排骨汤", ["排骨", "冬瓜", "姜"], "soup"),
    ("莲藕排骨汤", ["排骨", "莲藕", "胡萝卜"], "soup"),
    ("玉米排骨汤", ["排骨", "玉米", "胡萝卜"], "soup"),
    ("香菇鸡汤", ["鸡块", "香菇", "姜"], "soup"),
    ("紫菜蛋花汤", ["紫菜", "鸡蛋", "虾皮"], "soup"),
    ("酸辣汤", ["豆腐", "木耳", "鸡蛋"], "soup"),
    ("皮蛋瘦肉粥", ["大米", "皮蛋", "瘦肉"], "porridge"),
    ("海鲜粥", ["大米", "虾仁", "鱿鱼"], "porridge"),
    ("蛋炒饭", ["米饭", "鸡蛋", "葱"], "fried_rice"),
    ("扬州炒饭", ["米饭", "虾仁", "火腿"], "fried_rice"),
    ("牛肉炒饭", ["米饭", "牛肉", "洋葱"], "fried_rice"),
    ("腊味煲仔饭", ["大米", "腊肠", "腊肉"], "boil"),
    ("干炒牛河", ["河粉", "牛肉", "豆芽"], "stir_fry"),
    ("扬州炒面", ["面条", "鸡蛋", "火腿"], "stir_fry"),
    ("葱油拌面", ["面条", "小葱", "猪油"], "noodle"),
    ("炸酱面", ["面条", "猪肉末", "黄瓜"], "noodle"),
    ("西红柿鸡蛋面", ["面条", "番茄", "鸡蛋"], "noodle"),
    ("白菜猪肉饺子", ["面粉", "猪肉", "大白菜"], "dumpling"),
    ("韭菜鸡蛋饺子", ["面粉", "韭菜", "鸡蛋"], "dumpling"),
    ("三鲜水饺", ["面粉", "虾仁", "猪肉"], "dumpling"),
    ("猪肉大葱包子", ["面粉", "猪肉", "大葱"], "bun"),
    ("鲜肉小笼", ["面粉", "猪肉", "肉皮冻"], "bun"),
    ("葱油饼", ["面粉", "小葱", "猪油"], "pancake"),
    ("肉夹馍", ["猪肉", "白吉馍", "青椒"], "braise"),
    ("兰州牛肉面", ["拉面", "牛肉", "白萝卜"], "noodle"),
    ("重庆小面", ["面条", "猪肉末", "花生碎"], "noodle"),
    ("桂林米粉", ["米粉", "牛肉", "酸豆角"], "noodle"),
    ("酸辣粉", ["红薯粉", "花生", "酸菜"], "noodle"),
]


# 外国菜：5 个类别，每类 10 道
FOREIGN_CLASSICS: dict[str, list[tuple[str, list[str], str, list[str], str]]] = {
    "西餐": [
        ("意大利肉酱面", ["意面", "牛肉末", "番茄"], "pasta", ["不辣", "适合儿童"], "简单"),
        ("奶油培根意面", ["意面", "培根", "奶油"], "pasta", ["不辣"], "简单"),
        ("玛格丽特披萨", ["披萨面团", "番茄", "马苏里拉"], "pizza", ["不辣", "适合儿童"], "中等"),
        ("凯撒沙拉", ["生菜", "鸡胸肉", "面包丁"], "salad", ["不辣"], "简单"),
        ("煎牛排", ["牛排", "黄油", "迷迭香"], "grill", ["不辣"], "中等"),
        ("焗芝士通心粉", ["通心粉", "奶酪", "牛奶"], "bake", ["不辣", "适合儿童"], "简单"),
        ("经典汉堡", ["汉堡胚", "牛肉饼", "生菜"], "sandwich", ["不辣"], "简单"),
        ("炸鱼薯条", ["鳕鱼", "土豆", "面粉"], "deep_fry", ["不辣"], "中等"),
        ("法式洋葱汤", ["洋葱", "牛骨汤", "面包"], "soup", ["不辣"], "简单"),
        ("苹果派", ["苹果", "面粉", "黄油"], "dessert", ["不辣", "适合儿童"], "中等"),
    ],
    "日本菜": [
        ("日式咖喱饭", ["米饭", "鸡腿肉", "土豆"], "stew", ["不辣", "适合儿童"], "简单"),
        ("照烧鸡腿饭", ["鸡腿肉", "米饭", "西兰花"], "braise", ["不辣"], "简单"),
        ("亲子丼", ["鸡腿肉", "鸡蛋", "米饭"], "boil", ["不辣", "适合儿童"], "简单"),
        ("日式牛肉饭", ["牛肉片", "洋葱", "米饭"], "braise", ["不辣"], "简单"),
        ("寿喜锅", ["牛肉片", "白菜", "豆腐"], "boil", ["不辣"], "中等"),
        ("日式炸猪排", ["猪里脊", "鸡蛋", "面包糠"], "deep_fry", ["不辣"], "中等"),
        ("关东煮", ["白萝卜", "鱼丸", "鸡蛋"], "boil", ["不辣", "适合儿童"], "简单"),
        ("茶碗蒸", ["鸡蛋", "虾仁", "香菇"], "steam", ["不辣", "适合儿童"], "中等"),
        ("三文鱼饭团", ["米饭", "三文鱼", "海苔"], "boil", ["不辣", "适合儿童"], "简单"),
        ("味噌汤", ["豆腐", "海带", "蘑菇"], "soup", ["不辣", "适合儿童"], "简单"),
    ],
    "朝鲜菜": [
        ("韩式拌饭", ["米饭", "牛肉", "菠菜"], "stir_fry", ["辣"], "简单"),
        ("石锅拌饭", ["米饭", "牛肉", "豆芽"], "stir_fry", ["辣"], "中等"),
        ("韩式辣炒年糕", ["年糕", "鱼饼", "洋葱"], "stir_fry", ["辣"], "简单"),
        ("泡菜五花肉", ["五花肉", "泡菜", "洋葱"], "stir_fry", ["辣"], "简单"),
        ("韩式炸鸡", ["鸡翅", "鸡蛋", "淀粉"], "deep_fry", ["辣"], "中等"),
        ("部队火锅", ["午餐肉", "年糕", "方便面"], "boil", ["辣"], "简单"),
        ("海鲜葱饼", ["面粉", "鱿鱼", "小葱"], "pancake", ["不辣"], "中等"),
        ("韩式冷面", ["冷面", "牛肉", "黄瓜"], "noodle", ["不辣"], "中等"),
        ("紫菜包饭", ["米饭", "海苔", "火腿"], "roll", ["不辣", "适合儿童"], "简单"),
        ("大酱汤", ["豆腐", "西葫芦", "土豆"], "soup", ["不辣"], "简单"),
    ],
    "东南亚菜": [
        ("泰式冬阴功", ["虾", "蘑菇", "番茄"], "soup", ["辣"], "中等"),
        ("泰式菠萝炒饭", ["米饭", "菠萝", "虾仁"], "fried_rice", ["不辣"], "简单"),
        ("泰式青咖喱鸡", ["鸡腿肉", "椰奶", "土豆"], "stew", ["辣"], "中等"),
        ("越南牛肉河粉", ["河粉", "牛肉", "豆芽"], "noodle", ["不辣"], "简单"),
        ("越南春卷", ["米纸", "虾仁", "生菜"], "roll", ["不辣"], "简单"),
        ("海南鸡饭", ["鸡腿", "大米", "黄瓜"], "boil", ["不辣", "适合儿童"], "中等"),
        ("马来咖喱鸡", ["鸡腿肉", "土豆", "椰奶"], "stew", ["辣"], "中等"),
        ("新加坡炒米粉", ["米粉", "鸡蛋", "虾仁"], "stir_fry", ["不辣"], "简单"),
        ("印尼炒饭", ["米饭", "鸡蛋", "鸡肉"], "fried_rice", ["微辣"], "简单"),
        ("叻沙面", ["面条", "虾", "椰奶"], "noodle", ["辣"], "中等"),
    ],
    "其他地区": [
        ("西班牙海鲜饭", ["大米", "虾", "青口贝"], "boil", ["不辣"], "中等"),
        ("墨西哥鸡肉卷饼", ["卷饼", "鸡胸肉", "生菜"], "sandwich", ["辣"], "简单"),
        ("墨西哥牛肉塔可", ["玉米饼", "牛肉末", "生菜"], "stir_fry", ["辣"], "简单"),
        ("印度黄油鸡", ["鸡腿肉", "番茄", "奶油"], "stew", ["微辣"], "中等"),
        ("印度土豆咖喱", ["土豆", "洋葱", "番茄"], "stew", ["辣"], "简单"),
        ("土耳其烤肉卷", ["薄饼", "牛肉", "生菜"], "sandwich", ["不辣"], "中等"),
        ("俄式罗宋汤", ["牛肉", "甜菜根", "卷心菜"], "soup", ["不辣"], "中等"),
        ("德式土豆沙拉", ["土豆", "培根", "洋葱"], "salad", ["不辣"], "简单"),
        ("希腊沙拉", ["番茄", "黄瓜", "菲达奶酪"], "salad", ["不辣"], "简单"),
        ("中东鹰嘴豆泥拼饼", ["鹰嘴豆", "橄榄油", "皮塔饼"], "cold", ["不辣", "适合儿童"], "简单"),
    ],
}


SPICY_HINTS = ("辣", "麻", "水煮", "鱼香", "剁椒", "小面", "酸辣")
KID_FRIENDLY = {
    "西红柿炒鸡蛋",
    "番茄炒蛋",
    "蛋炒饭",
    "紫菜蛋花汤",
    "蒸蛋",
    "南瓜馒头",
    "白菜炖豆腐",
    "玉米排骨汤",
}

DIFFICULTY_BY_TECHNIQUE = {
    "stir_fry": "简单",
    "braise": "中等",
    "stew": "中等",
    "steam": "简单",
    "deep_fry": "中等",
    "boil": "简单",
    "soup": "简单",
    "porridge": "简单",
    "fried_rice": "简单",
    "noodle": "简单",
    "dumpling": "中等",
    "bun": "中等",
    "pancake": "中等",
    "cold": "简单",
    "roast": "进阶",
    "salad": "简单",
    "pasta": "简单",
    "pizza": "中等",
    "risotto": "中等",
    "bake": "中等",
    "sandwich": "简单",
    "grill": "中等",
    "dessert": "中等",
    "roll": "简单",
}


def _normalize_builtin_tags(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    for tag in tags:
        if tag == "微辣":
            t = "辣"
        else:
            t = tag
        if t not in normalized:
            normalized.append(t)
    if "辣" in normalized and "不辣" in normalized:
        normalized = [t for t in normalized if t != "不辣"]
    return normalized


def _infer_chinese_tags(name: str) -> list[str]:
    tags = ["辣"] if any(k in name for k in SPICY_HINTS) else ["不辣"]
    if name in KID_FRIENDLY and "不辣" in tags:
        tags.append("适合儿童")
    return tags


def build_builtin_recipes() -> dict[str, dict]:
    recipes: dict[str, dict] = {}

    for name, ingredients, technique in CHINESE_CLASSICS:
        recipes[name] = _build_entry(
            name=name,
            ingredients=ingredients,
            technique=technique,
            cuisine_group="中餐",
            cuisine="中餐经典",
            tags=_infer_chinese_tags(name),
            difficulty=DIFFICULTY_BY_TECHNIQUE.get(technique, DEFAULT_DIFFICULTY),
        )

    for cuisine in FOREIGN_CUISINE_OPTIONS:
        for name, ingredients, technique, tags, difficulty in FOREIGN_CLASSICS[cuisine]:
            recipes[name] = _build_entry(
                name=name,
                ingredients=ingredients,
                technique=technique,
                cuisine_group="外国菜",
                cuisine=cuisine,
                tags=_normalize_builtin_tags(tags),
                difficulty=difficulty,
            )

    return recipes


assert len(CHINESE_CLASSICS) == 100, f"中餐数量异常: {len(CHINESE_CLASSICS)}"
assert all(len(v) == 10 for v in FOREIGN_CLASSICS.values()), "外国菜子类数量异常"
assert sum(len(v) for v in FOREIGN_CLASSICS.values()) == 50, "外国菜总量异常"


BUILTIN_RECIPES: dict[str, dict] = build_builtin_recipes()
BUILTIN_RECIPE_COUNT = len(BUILTIN_RECIPES)
