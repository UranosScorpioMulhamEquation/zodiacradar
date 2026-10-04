import calendar
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
import pandas as pd
import streamlit as st
import swisseph as swe
import base64

# ==========================================
# 1. القواميس والمعطيات الفلكية الموسعة
# ==========================================

ZODIAC_SIGNS: Dict[int, Dict[str, Any]] = {
    0: {"ar": "الحمل", "en": "Aries", "element": "ناري", "ruler": "المريخ", "degrees": (0, 30)},
    1: {"ar": "الثور", "en": "Taurus", "element": "ترابي", "ruler": "الزهرة", "degrees": (30, 60)},
    2: {"ar": "الجوزاء", "en": "Gemini", "element": "هوائي", "ruler": "عطارد", "degrees": (60, 90)},
    3: {"ar": "السرطان", "en": "Cancer", "element": "مائي", "ruler": "القمر", "degrees": (90, 120)},
    4: {"ar": "الأسد", "en": "Leo", "element": "ناري", "ruler": "الشمس", "degrees": (120, 150)},
    5: {"ar": "العذراء", "en": "Virgo", "element": "ترابي", "ruler": "عطارد", "degrees": (150, 180)},
    6: {"ar": "الميزان", "en": "Libra", "element": "هوائي", "ruler": "الزهرة", "degrees": (180, 210)},
    7: {"ar": "العقرب", "en": "Scorpio", "element": "مائي", "ruler": "المريخ/بلوتو", "degrees": (210, 240)},
    8: {"ar": "القوس", "en": "Sagittarius", "element": "ناري", "ruler": "المشتري", "degrees": (240, 270)},
    9: {"ar": "الجدي", "en": "Capricorn", "element": "ترابي", "ruler": "زحل", "degrees": (270, 300)},
    10: {"ar": "الدلو", "en": "Aquarius", "element": "هوائي", "ruler": "زحل/أورانوس", "degrees": (300, 330)},
    11: {"ar": "الحوت", "en": "Pisces", "element": "مائي", "ruler": "المشتري/نبتون", "degrees": (330, 360)},
}

PLANET_MAP: Dict[str, int] = {
    "الشمس": swe.SUN,
    "عطارد": swe.MERCURY,
    "الزهرة": swe.VENUS,
    "المريخ": swe.MARS,
    "المشتري": swe.JUPITER,
    "زحل": swe.SATURN,
    "أورانوس": swe.URANUS,
    "نبتون": swe.NEPTUNE,
    "بلوتو": swe.PLUTO,
    "الراهو": swe.TRUE_NODE,
}

# قواميس التفسير الدقيق لطبيعة الكواكب وتأثيراتها
PLANET_NATURE: Dict[str, Dict[str, str]] = {
    "الشمس": {"role": "الإشراق والظهور", "impact": "تسلط الضوء وتمنح الحيوية والنجاح الملحوظ وتكشف الخفايا."},
    "عطارد": {"role": "العقل والاتصال", "impact": "يسرّع وتيرة الأخبار، المفاوضات، العقود، والنشاط الذهني."},
    "الزهرة": {"role": "الجاذبية والوفرة", "impact": "تجلب الانسجام العاطفي، السيولة المالية، وتيسير الأمور بسلاسة."},
    "المريخ": {"role": "الطاقة والمبادرة", "impact": "يمنح الشجاعة والدافع، ولكنه قد يسبب احتكاكات وتسرع إن لم يُوجّه بحكمة."},
    "المشتري": {"role": "التوسع والحظ", "impact": "يضاعف الفرص، يجلب الحماية الفلكية، ويفتح آفاقاً جديدة للنمو."},
    "زحل": {"role": "الهيكلة والدروس", "impact": "يفرض قيوداً لاختبار الصبر، يطالب بالانضباط، ويبني أساسات متينة للمستقبل."},
    "أورانوس": {"role": "التمرد والمفاجآت", "impact": "يكسر الروتين بأحداث غير متوقعة، يحرر من القيود، ويجلب فرصاً مفاجئة."},
    "نبتون": {"role": "الإلهام والوهم", "impact": "يزيد من الحساسية والروحانية، لكنه يطالب بالحذر من الخداع وضبابية الرؤية."},
    "بلوتو": {"role": "التحول الجذري", "impact": "ينهي مرحلة بشكل قاطع ليبدأ أخرى، يطهر الطاقات، ويمنح قوة تأثير عميقة."},
    "الراهو": {"role": "القدر والجوع الكارمي", "impact": "يدفعك بقوة هائلة نحو مسارات جديدة غير مألوفة، ويجلب تطورات مفصلية."}
}

ASPECTS: Dict[int, Dict[str, Any]] = {
    0: {"name": "اقتران", "nature": "قوي ومكثف", "symbol": "☌", "weight": 5, 
        "meaning": "اندماج طاقي تام. إذا كان مع كوكب سعود (كالمشتري) فهو انتصار، ومع نحس (كزحل) هو ضغط مركز يطالب بالحسم."},
    60: {"name": "تسديس", "nature": "إيجابي وداعم", "symbol": "⚹", "weight": 2, 
        "meaning": "فرص مواتية تلوح في الأفق، تتطلب منك خطوات عملية لالتقاطها. انسجام يسهل التواصل."},
    90: {"name": "تربيع", "nature": "تحدي واحتكاك", "symbol": "□", "weight": -4, 
        "meaning": "زاوية حرجة تولّد طاقة ضغط عالية. إجبار على الخروج من منطقة الراحة واتخاذ قرارات مصيرية لتجاوز العقبات."},
    120: {"name": "تثليث", "nature": "حماية وتدفق سلس", "symbol": "△", "weight": 4, 
        "meaning": "أفضل زوايا الحظ. تدفق سلس للطاقة، تيسير للأمور المعقدة، وحماية فلكية من الأزمات."},
    180: {"name": "مقابلة", "nature": "مواجهة واستقطاب", "symbol": "☍", "weight": -3, 
        "meaning": "حالة شد وجذب. تبرز خلافات أو تسويات حتمية مع الآخرين (شراكات، خصوم). تتطلب التوازن وعدم التطرف."},
}

HOUSE_INTERPRETATIONS: Dict[int, Dict[str, str]] = {
    1: {"domain": "الذات، الحيوية، والمبادرات الشخصية", 
        "fin": "قرارات مالية تعتمد على جهدك الشخصي البحت.", "car": "صدارة في المشهد المهني وفرض لشروطك.", "lov": "جاذبية عالية وبداية لفتح صفحة جديدة لنفسك.", "hea": "طاقة بدنية تتجدد، أو ضرورة الانتباه للإجهاد الناتج عن فرط النشاط."},
    2: {"domain": "الموارد، السيولة المالية، والمكتسبات", 
        "fin": "تركيز فلكي مكثف على مصادر الدخل وإعادة تقييم ميزانيتك.", "car": "مردود مادي لجهودك المهنية السابقة.", "lov": "بحث عن الأمان العاطفي والاستقرار.", "hea": "استقرار بدني يعتمد على نوعية الغذاء."},
    3: {"domain": "العقود، التواصل، والسفر القصير", 
        "fin": "أرباح من تجارة سريعة، مبيعات، أو أعمال كتابية.", "car": "اجتماعات مكثفة وتوقيع عقود هامة.", "lov": "تقارب فكري وتواصل صريح يحل الخلافات.", "hea": "نشاط ذهني زائد قد يؤدي إلى أرق أو توتر عصبي."},
    4: {"domain": "العائلة، الجذور، والعقارات", 
        "fin": "استثمارات عقارية أو أموال مرتبطة بالأسرة.", "car": "العمل من المنزل أو تأسيس قاعدة مهنية صلبة.", "lov": "التركيز على الحياة الخاصة والروابط الأسرية الحميمة.", "hea": "حاجة للراحة النفسية والابتعاد عن صخب العالم."},
    5: {"domain": "المخاطرة، الإبداع، والعاطفة", 
        "fin": "أرباح من استثمارات جريئة أو مشاريع شخصية إبداعية.", "car": "تألق وإثبات للقدرات بأسلوب مبتكر.", "lov": "فترة ذهبية للرومانسية، شرارة إعجاب، أو تجديد لشغف العلاقة.", "hea": "طاقة ممتازة للرياضة والترفيه وتفريغ الضغوط."},
    6: {"domain": "الروتين، الواجبات المهنية، والصحة", 
        "fin": "دخل مستقر ناتج عن عمل يومي دؤوب.", "car": "تراكم للمهام يتطلب تنظيماً شديداً، وتغييرات في بيئة العمل.", "lov": "دعم الشريك في المهام اليومية، أو التعرف على شخص عبر بيئة العمل.", "hea": "بيت الصحة المباشر؛ يتطلب فحوصات روتينية ونظاماً غذائياً صارماً."},
    7: {"domain": "الشراكات، العقود الرسمية، والزواج", 
        "fin": "أرباح أو التزامات مالية ناتجة عن شراكة مهنية.", "car": "مفاوضات هامة، وتسويات مع منافسين أو شركاء.", "lov": "محور العلاقات؛ قرارات حاسمة بالارتباط الرسمي أو فض الشراكات غير المجدية.", "hea": "الحالة الصحية تتأثر بالاستقرار النفسي مع المحيطين."},
    8: {"domain": "التحولات، أموال الآخرين، والديون", 
        "fin": "تسويات بنكية، ضرائب، تركات، أو حصول على تمويل ودعم مالي خارجي.", "car": "تغيير جذري في مسار العمل أو إنهاء حقبة مهنية.", "lov": "علاقات عميقة، غيرة، أو شغف شديد ومرحلة تحول نفسي.", "hea": "فترة استشفاء وتجديد للخلايا، أو حاجة لعمليات جراحية بسيطة للتعافي."},
    9: {"domain": "الآفاق، السفر البعيد، والقضايا", 
        "fin": "مكاسب من تعاملات خارجية أو أعمال استيراد وتصدير.", "car": "ترقية، دراسات عليا تدعم المهنة، أو نجاح في قضايا قانونية.", "lov": "انجذاب لأشخاص من خلفيات ثقافية مختلفة.", "hea": "تعافي سريع وحيوية مستمدة من تغيير الأجواء والأسفار."},
    10: {"domain": "السمعة، الإنجازات الكبرى، والسلطة", 
        "fin": "ترقية مالية مرتبطة بتطور المركز الاجتماعي.", "car": "أهم بيوت المهنة؛ تسليط الضوء على إنجازاتك، اعتراف بجهودك، أو تحديات مع السلطات.", "lov": "ارتباط شخصي يؤثر على صورتك الاجتماعية.", "hea": "ضغوط الهيكل العظمي أو الإرهاق بسبب تحمل مسؤوليات جسيمة."},
    11: {"domain": "الشبكات الاجتماعية، الدعم، والأماني", 
        "fin": "عوائد مالية من مشاريع جماعية أو مهنة حرة.", "car": "دعم من شخصيات نافذة أو نجاح من خلال العمل الجماهيري.", "lov": "تحول صداقات إلى علاقات عاطفية، وتناغم مع الشريك.", "hea": "حالة صحية جيدة مدعومة بالطاقة الإيجابية من الأصدقاء."},
    12: {"domain": "العزلة، الإغلاقات، واللاوعي", 
        "fin": "مصاريف غير متوقعة أو أموال تأتي من مصادر خفية.", "car": "العمل خلف الكواليس، التحضير لمشروع سري، أو إنهاء مرحلة مهنية.", "lov": "علاقات سرية، أو حاجة للابتعاد قليلاً لتقييم العلاقة بهدوء.", "hea": "تحذير فلكي للإرهاق؛ ضرورة العزلة، النوم الكافي، والتأمل لتفريغ السموم النفسية والجسدية."}
}

# ==========================================
# 2. المحرك الفلكي (Swiss Ephemeris Engine)
# ==========================================

class AstrologyEngine:
    def __init__(self):
        swe.set_ephe_path("")

    @staticmethod
    def get_julian_day(year: int, month: int, day: int, hour: float = 12.0) -> float:
        return swe.julday(year, month, day, hour)

    @staticmethod
    def get_ecliptic_longitude(jd: float, planet_id: int) -> float:
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        res, _ = swe.calc_ut(jd, planet_id, flags)
        return res[0]

    @staticmethod
    def get_sign_from_longitude(lon: float) -> Tuple[int, float]:
        sign_index = int(lon // 30)
        degree_in_sign = lon % 30
        return sign_index, degree_in_sign

    def calculate_whole_sign_house(self, target_sign_idx: int, planet_sign_idx: int) -> int:
        return ((planet_sign_idx - target_sign_idx) % 12) + 1

    def calculate_aspect(self, target_sign_idx: int, planet_sign_idx: int) -> Tuple[int, Dict[str, Any]]:
        diff = abs(planet_sign_idx - target_sign_idx) % 12
        if diff > 6:
            diff = 12 - diff
        exact_deg = diff * 30
        
        return exact_deg, ASPECTS.get(
            exact_deg,
            {"name": "لا يوجد اتصال رئيسي", "nature": "محايد", "symbol": "-", "weight": 0, "meaning": ""}
        )

    def detect_lunar_phases_and_eclipses(self, year: int, month: int) -> List[Dict[str, Any]]:
        events = []
        num_days = calendar.monthrange(year, month)[1]
        prev_angle = None
        
        for day in range(1, num_days + 1):
            jd = self.get_julian_day(year, month, day, 12.0)
            sun_lon = self.get_ecliptic_longitude(jd, swe.SUN)
            moon_lon = self.get_ecliptic_longitude(jd, swe.MOON)
            node_lon = self.get_ecliptic_longitude(jd, swe.TRUE_NODE)
            angle = (moon_lon - sun_lon) % 360

            if prev_angle is not None:
                if prev_angle > 330 and angle < 30: # ولادة
                    sign_idx, deg = self.get_sign_from_longitude(sun_lon)
                    is_eclipse = min(abs(sun_lon - node_lon), abs(sun_lon - (node_lon + 180) % 360)) < 18.0
                    events.append({"type": "كسوف شمس حلقي/كلي" if is_eclipse else "ولادة قمر جديد", 
                                   "day": day, "sign_index": sign_idx, "degree": deg})
                elif prev_angle < 180 and angle >= 180: # اكتمال
                    sign_idx, deg = self.get_sign_from_longitude(moon_lon)
                    is_eclipse = min(abs(moon_lon - node_lon), abs(moon_lon - (node_lon + 180) % 360)) < 15.0
                    events.append({"type": "خسوف قمر" if is_eclipse else "اكتمال قمر (بدر)", 
                                   "day": day, "sign_index": sign_idx, "degree": deg})
            prev_angle = angle
        return events

    def detect_outer_ingresses(self, year: int, month: int) -> List[Dict[str, Any]]:
        ingresses = []
        outer_planets = {"المشتري": swe.JUPITER, "زحل": swe.SATURN, "أورانوس": swe.URANUS,
                         "نبتون": swe.NEPTUNE, "بلوتو": swe.PLUTO, "الراهو": swe.TRUE_NODE}

        for name, planet_id in outer_planets.items():
            jd_start = self.get_julian_day(year, month, 1)
            jd_end = self.get_julian_day(year, month, calendar.monthrange(year, month)[1])
            sign_start, _ = self.get_sign_from_longitude(self.get_ecliptic_longitude(jd_start, planet_id))
            sign_end, deg_end = self.get_sign_from_longitude(self.get_ecliptic_longitude(jd_end, planet_id))

            if sign_start != sign_end:
                is_retrograde = (planet_id == swe.TRUE_NODE)
                ingresses.append({
                    "planet": name, "new_sign_index": sign_end, "degree": deg_end,
                    "degree_text": "الدرجة 29° (حركة تراجعية للمحور)" if is_retrograde else "الدرجة 0° (نقطة الصفر الكارمية)",
                    "description": PLANET_NATURE[name]["impact"]
                })
        return ingresses


# ==========================================
# 3. محرك التفسير والاستخراج (Interpretation Engine)
# ==========================================

class PredictionGenerator:
    def __init__(self, engine: AstrologyEngine):
        self.engine = engine

    def generate_monthly_report(self, target_sign_idx: int, year: int, month: int) -> Dict[str, Any]:
        mid_month_jd = self.engine.get_julian_day(year, month, 15)

        # حساب مواضع جميع الكواكب العابرة واتصالاتها مع الطالع المستهدف
        transits = {}
        for name, planet_id in PLANET_MAP.items():
            lon = self.engine.get_ecliptic_longitude(mid_month_jd, planet_id)
            sign_idx, deg = self.engine.get_sign_from_longitude(lon)
            house = self.engine.calculate_whole_sign_house(target_sign_idx, sign_idx)
            aspect_deg, aspect_data = self.engine.calculate_aspect(target_sign_idx, sign_idx)
            
            transits[name] = {
                "sign_index": sign_idx, "degree": deg, "house": house, 
                "aspect_deg": aspect_deg, "aspect": aspect_data, "nature": PLANET_NATURE[name]
            }

        lunar_events = self.engine.detect_lunar_phases_and_eclipses(year, month)
        ingresses = self.engine.detect_outer_ingresses(year, month)

        return {
            "financial": self._build_domain_forecast(transits, "fin", ["الزهرة", "المشتري"], [2, 8]),
            "career": self._build_domain_forecast(transits, "car", ["الشمس", "عطارد", "المريخ", "زحل"], [10, 6]),
            "love": self._build_domain_forecast(transits, "lov", ["الزهرة", "المريخ", "بلوتو"], [5, 7]),
            "health": self._build_domain_forecast(transits, "hea", ["زحل", "المريخ", "نبتون", "أورانوس"], [1, 6, 12]),
            "emergency": self._build_emergency_forecast(ingresses, lunar_events, target_sign_idx),
            "advice_warnings": self._build_advice_and_warnings(transits),
            "raw_transits": transits,
        }

    def _build_domain_forecast(self, transits, domain_key: str, key_planets: List[str], key_houses: List[int]) -> str:
        paragraphs = []
        
        # 1. تحليل الكواكب الموجودة في البيوت المعنية بالمجال
        occupants = [p for p, d in transits.items() if d["house"] in key_houses]
        if occupants:
            for p in occupants:
                h = transits[p]["house"]
                paragraphs.append(f"• **عبور {p} في البيت {h} ({HOUSE_INTERPRETATIONS[h]['domain']}):** {HOUSE_INTERPRETATIONS[h][domain_key]} كوكب {p} هنا {PLANET_NATURE[p]['impact']}")
        
        # 2. تحليل اتصالات الكواكب الحاكمة للمجال (إذا لم تكن في بيوت المجال)
        for kp in key_planets:
            if kp not in occupants:
                h = transits[kp]["house"]
                asp = transits[kp]["aspect"]
                if asp["name"] != "لا يوجد اتصال رئيسي":
                    paragraphs.append(f"• **تأثير {kp} (من البيت {h}):** يشكل زاوية {asp['name']} ({asp['symbol']}) مع برجك. {asp['meaning']} {PLANET_NATURE[kp]['impact']}")
        
        if not paragraphs:
            paragraphs.append("• المؤشرات الفلكية المباشرة هادئة في هذا القطاع، مما يعني استقراراً مبنياً على قراراتك السابقة دون ضغوط فلكية كبرى.")
            
        return "\n\n".join(paragraphs)

    def _build_emergency_forecast(self, ingresses, lunar_events, target_sign_idx) -> List[str]:
        alerts = []
        
        for ing in ingresses:
            rel_house = self.engine.calculate_whole_sign_house(target_sign_idx, ing["new_sign_index"])
            domain = HOUSE_INTERPRETATIONS[rel_house]['domain']
            alerts.append(f"🚨 **انتقال تاريخي لـ {ing['planet']} إلى برج {ZODIAC_SIGNS[ing['new_sign_index']]['ar']} ({ing['degree_text']}):** "
                          f"يستهدف (البيت {rel_house} - {domain}). حدث جيلي يفرض تغييرات طويلة الأمد. {ing['description']}")

        for event in lunar_events:
            rel_house = self.engine.calculate_whole_sign_house(target_sign_idx, event["sign_index"])
            domain = HOUSE_INTERPRETATIONS[rel_house]['domain']
            sign_name = ZODIAC_SIGNS[event['sign_index']]['ar']
            
            if "كسوف" in event["type"]:
                desc = f"طاقة مكثفة لإغلاق باب وفتح آخر رغماً عن الإرادة في ملفات ({domain}). الانتباه المالي والصحي واجب."
                icon = "🌑⚠️"
            elif "خسوف" in event["type"]:
                desc = f"بلوغ ذروة كارمية، إغلاق ملفات عالقة، وحسم نهائي لقصة تخص ({domain})."
                icon = "🌕⚠️"
            elif "ولادة" in event["type"]:
                desc = f"وقت مثالي ومبارك لزرع نوايا جديدة والانطلاق بمشاريع تخص ({domain})."
                icon = "🌑✨"
            else:
                desc = f"تتجلى الحقائق وتكتمل الجهود السابقة. حصاد النتائج في أمور تتعلق بـ ({domain})."
                icon = "🌕🔍"
            alerts.append(f"{icon} **{event['type']} في برج {sign_name} (البيت {rel_house}):** {desc}")

        if not alerts:
            alerts.append("لا توجد تحركات كوكبية ثقيلة (Ingresses) أو خسوف/كسوف خلال هذا الشهر.")
        return alerts

    def _build_advice_and_warnings(self, transits) -> Dict[str, List[str]]:
        advice = []
        warnings = []
        
        for p_name, data in transits.items():
            asp = data["aspect"]
            house_dom = HOUSE_INTERPRETATIONS[data['house']]['domain']
            
            # فلترة الزوايا السلبية أو الصعبة
            if asp["weight"] < 0:
                warnings.append(f"⚠️ **{asp['name']} {p_name} من (البيت {data['house']}):** {asp['meaning']} احذر من التسرع أو التصادم في قضايا ({house_dom}).")
            
            # اقتران الكواكب الصعبة
            elif asp["name"] == "اقتران" and p_name in ["زحل", "المريخ", "بلوتو", "أورانوس", "الراهو"]:
                warnings.append(f"⚠️ **اقتران {p_name} ببرجك:** زاوية ضغط هائلة لإعادة الهيكلة. {PLANET_NATURE[p_name]['impact']} حافظ على هدوئك.")
                
            # الزوايا الإيجابية والداعمة
            elif asp["weight"] > 0 or (asp["name"] == "اقتران" and p_name in ["المشتري", "الزهرة", "الشمس", "عطارد"]):
                advice.append(f"💡 **{asp['name']} {p_name} من (البيت {data['house']}):** طاقة حماية وداعمة. {asp['meaning']} استغلها في ملفات ({house_dom}).")

        if not warnings:
            warnings.append("العبور الفلكي خالٍ من الزوايا الضاغطة المباشرة، فترة ممتازة للتقدم بأمان.")
        if not advice:
            advice.append("الاعتماد هذا الشهر على مجهودك الذاتي بشكل كامل، الكواكب في مواقع محايدة.")
            
        return {"advice": advice, "warnings": warnings}


# ==========================================
# 4. توليد تقرير HTML المنسق
# ==========================================

def create_html_report(report_data: Dict, sign_name: str, year: int, month: int) -> str:
    def list_to_html(lst):
        return "".join([f"<li style='margin-bottom: 8px;'>{item}</li>" for item in lst])
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>التقرير الفلكي الشامل - {sign_name}</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.8; color: #1a1a1a; padding: 20px; background: #f4f6f9; }}
            .container {{ max-width: 900px; margin: auto; background: #fff; padding: 40px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 5px solid #2c3e50; }}
            h1 {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 15px; }}
            h2 {{ color: #2980b9; font-size: 1.3em; margin-top: 30px; border-right: 4px solid #3498db; padding-right: 10px; }}
            .content-box {{ background: #fdfefe; padding: 15px; border-radius: 5px; border: 1px solid #e1e8ed; margin-bottom: 20px; }}
            ul {{ padding-right: 25px; }}
            .warning {{ color: #c0392b; }}
            .advice {{ color: #27ae60; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>التحليل الفلكي التفصيلي لبرج {sign_name}<br><small>شهر {month} / {year}</small></h1>
            
            <h2>💰 التحليل المالي والموارد</h2>
            <div class="content-box">{(report_data['financial'].replace('•', '<br>•'))}</div>
            
            <h2>💼 التحليل المهني ومسار العمل</h2>
            <div class="content-box">{(report_data['career'].replace('•', '<br>•'))}</div>
            
            <h2>❤️ التحليل العاطفي والشراكات</h2>
            <div class="content-box">{(report_data['love'].replace('•', '<br>•'))}</div>
            
            <h2>🏥 التحليل الصحي والطاقة البدنية</h2>
            <div class="content-box">{(report_data['health'].replace('•', '<br>•'))}</div>
            
            <h2>🚨 الأحداث الطارئة (خسوف/كسوف/كواكب جيلية)</h2>
            <div class="content-box"><ul>{list_to_html(report_data['emergency'])}</ul></div>
            
            <h2>💡 الإرشادات والفرص الفلكية</h2>
            <div class="content-box advice"><ul>{list_to_html(report_data['advice_warnings']['advice'])}</ul></div>
            
            <h2>⚠️ التحذيرات والزوايا الحرجة</h2>
            <div class="content-box warning"><ul>{list_to_html(report_data['advice_warnings']['warnings'])}</ul></div>
        </div>
    </body>
    </html>
    """
    return html

def get_html_download_link(html_content: str, filename: str, link_text: str) -> str:
    b64 = base64.b64encode(html_content.encode('utf-8')).decode()
    return f'<a href="data:text/html;charset=utf-8;base64,{b64}" download="{filename}" style="display: inline-block; padding: 0.6em 1.2em; color: white; background-color: #2c3e50; text-decoration: none; border-radius: 5px; font-weight: bold; border: 1px solid #1a252f; transition: 0.3s;">{link_text}</a>'


# ==========================================
# 5. واجهة المستخدم (Streamlit UI)
# ==========================================

def main():
    st.set_page_config(page_title="المحرك الفلكي الاحترافي", page_icon="🔭", layout="wide")

    st.title("🔭 منظومة التوقعات الفلكية العميقة لزوايا العبور")
    st.caption("برمجة الفلكي الدكتور : استرو رادار")
    st.markdown("---")

    st.sidebar.header("⚙️ إعدادات الحساب الفلكي")
    selected_sign_name = st.sidebar.selectbox("اختر البرج / الطالع:", options=[d["ar"] for d in ZODIAC_SIGNS.values()])
    target_sign_idx = [k for k, v in ZODIAC_SIGNS.items() if v["ar"] == selected_sign_name][0]
    
    selected_year = st.sidebar.number_input("اختر السنة:", min_value=1900, max_value=2100, value=2026, step=1)
    selected_month = st.sidebar.selectbox("اختر الشهر:", options=list(range(1, 13)), index=9)

    if st.sidebar.button("🚀 توليد التقرير الفلكي", type="primary"):
        engine = AstrologyEngine()
        generator = PredictionGenerator(engine)

        with st.spinner("جاري معالجة الخوارزميات الفلكية، وحساب زوايا العبور الدقيقة..."):
            report = generator.generate_monthly_report(target_sign_idx, selected_year, selected_month)

        c1, c2, c3 = st.columns(3)
        c1.metric("البرج المستهدف", ZODIAC_SIGNS[target_sign_idx]["ar"])
        c2.metric("الحاكم / العنصر", f"{ZODIAC_SIGNS[target_sign_idx]['ruler']} / {ZODIAC_SIGNS[target_sign_idx]['element']}")
        c3.metric("تاريخ الرصد", f"{selected_month} / {selected_year}")

        st.markdown("---")
        sign_ar = ZODIAC_SIGNS[target_sign_idx]["ar"]
        html_report = create_html_report(report, sign_ar, selected_year, selected_month)
        st.markdown(get_html_download_link(html_report, f"Astrology_Report_{sign_ar}_{selected_year}_{selected_month}.html", "📄 تصدير التقرير الاحترافي الكامل (HTML/PDF)"), unsafe_allow_html=True)
        st.markdown("---")

        t1, t2, t3, t4, t5, t6 = st.tabs([
            "💰 المال", "💼 العمل", "❤️ العاطفة", "🏥 الصحة", "🚨 الأحداث والتحذيرات", "📊 مصفوفة العبور"
        ])

        with t1:
            st.info(report["financial"])
        with t2:
            st.success(report["career"])
        with t3:
            st.write(report["love"])
        with t4:
            st.warning(report["health"])
        with t5:
            st.subheader("الأحداث المفصلية (خسوف/كسوف/حركة الأقطاب)")
            for a in report["emergency"]: st.markdown(f"- {a}")
            st.markdown("---")
            st.subheader("💡 فرص فلكية ذهبية")
            for a in report["advice_warnings"]["advice"]: st.markdown(f"- {a}")
            st.markdown("---")
            st.subheader("⚠️ تحذيرات وزوايا حرجة (تربيع / مقابلة)")
            for w in report["advice_warnings"]["warnings"]: st.markdown(f"- {w}")
        with t6:
            df = pd.DataFrame([{
                "الكوكب": p,
                "طبيعة التأثير": d["nature"]["role"],
                "البرج العابر": ZODIAC_SIGNS[d["sign_index"]]["ar"],
                "الدرجة": f"{d['degree']:.2f}°",
                "البيت الشمسي": f"البيت {d['house']}",
                "الزاوية مع الطالع": f"{d['aspect']['name']} ({d['aspect']['symbol']})"
            } for p, d in report["raw_transits"].items()])
            st.dataframe(df, width='stretch')

if __name__ == "__main__":
    main()