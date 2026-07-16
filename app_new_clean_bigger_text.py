import html
from datetime import datetime

import requests
import streamlit as st
import streamlit.components.v1 as components

GOLD_PRICE = 4500
WORK_VYSHYVANKA = 3100
WORK_INDIVIDUAL = 3000
WORK_RING = 6100
PACKAGING = 3000
K = 13

GOLD_TYPES = ["Червоне", "Лимонне", "Біле", "Рожеве"]
COATING_OPTIONS = {
    "Без покриття": 0,
    "Родій 50$": 50,
    "Родій 100$": 100,
    "Рутеній 50$": 50,
    "Рутеній 100$": 100,
    "Емаль 100$": 100,
    "Емаль 200$": 200,
}


def get_coating_name(coating_option):
    if coating_option == "Без покриття":
        return "Без покриття"
    return coating_option.replace(" 50$", "").replace(" 100$", "").replace(" 200$", "")

STONE_PRICES_USD = {
    "Натуральні діаманти": {"1 мм": 9, "1.25 мм": 15, "1.5 мм": 24, "1.75 мм": 42, "2 мм": 55, "2.5 мм": 100, "3 мм": 220, "3.5 мм": 380, "4 мм": 800},
    "Лабораторні діаманти": {"1 мм": 7, "1.25 мм": 10, "1.5 мм": 15, "1.75 мм": 30, "2 мм": 30, "2.5 мм": 60, "3 мм": 140, "3.5 мм": 210, "4 мм": 390},
    "Муасаніти": {"1 мм": 5, "1.25 мм": 7, "1.5 мм": 9, "1.75 мм": 14, "2 мм": 16, "2.5 мм": 30, "3 мм": 60, "3.5 мм": 104, "4 мм": 154},
}


def get_usd_rate():
    try:
        url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
        data = requests.get(url, timeout=5).json()
        for item in data:
            if item.get("cc") == "USD":
                return float(item.get("rate"))
    except Exception:
        pass
    return 44.5


def money(value):
    return f"{value:,.0f}".replace(",", " ")


def money100(value):
    value = round(value / 100) * 100
    return f"{value:,.0f}".replace(",", " ")


def calc_weight(size, width, thickness):
    w = width / 10
    t = thickness / 10
    length = ((size * 3.14) / 10) + (thickness / 10) * 3
    return length * w * t * K


def get_work_price(product_type, design=None):
    if product_type == "Каблучка":
        return WORK_RING
    if design == "Вишиванка":
        return WORK_VYSHYVANKA
    return WORK_INDIVIDUAL


def get_stone_cost_by_type(stone_type, stone_size, qty, usd_rate):
    if qty <= 0:
        return 0, 0
    price_usd = STONE_PRICES_USD[stone_type][stone_size]
    total_usd = price_usd * qty
    total_uah = total_usd * usd_rate
    return total_usd, total_uah


def make_inserts_text(main_size, main_qty, small_size, small_qty):
    parts = []
    if main_qty > 0:
        parts.append(f"{main_size} - {main_qty} шт")
    if small_qty > 0:
        parts.append(f"{small_size} - {small_qty} шт")
    return "; ".join(parts) if parts else "не додано"


def calculate_wedding_rings(data):
    usd_rate = get_usd_rate()

    size_1 = data["size_1"]
    width_1 = data["width_1"]
    thickness_1 = data["thickness_1"]
    use_second_ring = data.get("use_second_ring", True)
    size_2 = data["size_2"] if use_second_ring else 0
    width_2 = data["width_2"] if use_second_ring else 0
    thickness_2 = data["thickness_2"] if use_second_ring else 0

    design = data["design"]
    gold_type = data.get("gold_type", "Біле")
    coating_option = data.get("coating_option", "Без покриття")
    coating_usd = COATING_OPTIONS.get(coating_option, 0)
    coating_name = get_coating_name(coating_option)
    coating_uah = coating_usd * usd_rate
    engraving = data["engraving"]
    delivery = data["delivery"]
    discount_percent = data["discount_percent"]

    ring_stone_enabled = data["ring_stone_enabled"]
    ring_stone_size = data["ring_stone_size"]
    ring_stone_qty = data["ring_stone_qty"] if ring_stone_enabled else 0

    manual_weight_1 = data.get("manual_weight_1", 0)
    manual_weight_2 = data.get("manual_weight_2", 0)

    auto_weight_1 = calc_weight(size_1, width_1, thickness_1)
    auto_weight_2 = calc_weight(size_2, width_2, thickness_2) if use_second_ring else 0

    weight_1 = manual_weight_1 if manual_weight_1 > 0 else auto_weight_1
    weight_note_1 = "Вага виробу 1 задана вручну" if manual_weight_1 > 0 else "Вага виробу 1 розрахована автоматично"

    if use_second_ring:
        weight_2 = manual_weight_2 if manual_weight_2 > 0 else auto_weight_2
        weight_note_2 = "Вага виробу 2 задана вручну" if manual_weight_2 > 0 else "Вага виробу 2 розрахована автоматично"
    else:
        weight_2 = 0
        weight_note_2 = "Друга обручка не додана"

    total_weight = weight_1 + weight_2

    work_per_gram = get_work_price("Пара обручок", design)
    work_cost = total_weight * work_per_gram
    discount = work_cost * (discount_percent / 100)
    work_after_discount = work_cost - discount
    gold_cost = total_weight * GOLD_PRICE
    base_total_without_stones = gold_cost + work_after_discount + PACKAGING + engraving + coating_uah + delivery

    stones_usd, stones_uah = get_stone_cost_by_type("Натуральні діаманти", ring_stone_size, ring_stone_qty, usd_rate)
    total = base_total_without_stones + stones_uah

    title = "Індивідуальна модель обручок «Вишиванка» ⚜️" if design == "Вишиванка" else "Індивідуальна модель обручок ⚜️"
    coating_client = coating_name
    inserts_text = f"{ring_stone_size} - {ring_stone_qty} шт" if ring_stone_qty > 0 else "не додано"

    second_weight_text = f"\n{weight_note_2}:\n{weight_2:.2f} г\n" if use_second_ring else ""
    if use_second_ring:
        client_sizes_text = f"Розміри: {size_1:g} та {size_2:g}"
        client_width_text = f"Ширина: {width_1:g} мм та {width_2:g} мм"
    else:
        client_sizes_text = f"Розмір: {size_1:g}"
        client_width_text = f"Ширина: {width_1:g} мм"

    technical_text = f"""Курс USD: {usd_rate:.2f} грн

Тип виробу:
Пара обручок

Тип золота:
{gold_type} золото 585 проби

Покриття вибране:
{coating_option}

{weight_note_1}:
{weight_1:.2f} г
{second_weight_text}
Загальна вага:
{total_weight:.2f} г

Золото:
{money(gold_cost)} грн

Робота:
{money(work_cost)} грн

Знижка:
-{money(discount)} грн

Робота після знижки:
{money(work_after_discount)} грн

Упаковка:
{money(PACKAGING)} грн

Гравіювання:
{money(engraving)} грн

Покриття:
{money(coating_uah)} грн

Діаманти / каміння:
{money(stones_uah)} грн ({stones_usd}$)

Доставка:
{money(delivery)} грн

=====================
ДО СПЛАТИ:
{money(total)} грн
"""

    client_text = f"""{title}

{gold_type} золото 585 проби 💍
{client_sizes_text}
{client_width_text}
Покриття: {coating_client}
Середня вага виробу: {total_weight:.1f} г
"""

    if ring_stone_qty > 0:
        variant_totals = {}
        for stone_type in STONE_PRICES_USD.keys():
            _, stone_uah_variant = get_stone_cost_by_type(stone_type, ring_stone_size, ring_stone_qty, usd_rate)
            variant_totals[stone_type] = base_total_without_stones + stone_uah_variant
        client_text += f"""Вставки: {inserts_text}

Середня вартість виробу:
• з натуральними діамантами:
{money100(variant_totals["Натуральні діаманти"])} грн 💎
• з лабораторними діамантами:
{money100(variant_totals["Лабораторні діаманти"])} грн 💎
• з муасанітами:
{money100(variant_totals["Муасаніти"])} грн 💎
"""
        poster_price = money100(variant_totals["Натуральні діаманти"])
    else:
        client_text += f"""
Середня вартість виробу:
{money100(total)} грн 💎
"""
        poster_price = money100(total)

    receipt_data = {
        "title": title.replace("⚜️", "").strip(),
        "gold_type": f"{gold_type} золото 585 проби",
        "sizes": client_sizes_text.replace("Розміри: ", "").replace("Розмір: ", ""),
        "width": client_width_text.replace("Ширина: ", ""),
        "coating": coating_client,
        "weight": f"{total_weight:.1f} г",
        "inserts": inserts_text,
        "gold_cost": gold_cost,
        "work_cost": work_cost,
        "discount": discount,
        "packaging": PACKAGING,
        "engraving": engraving,
        "coating_cost": coating_uah,
        "stones_cost": stones_uah,
        "delivery": delivery,
        "total": total,
    }
    return technical_text, client_text, receipt_data


def calculate_ring(data):
    usd_rate = get_usd_rate()

    size = data["size"]
    width = data["width"]
    thickness = data["thickness"]
    gold_type = data.get("gold_type", "Біле")
    coating_option = data.get("coating_option", "Без покриття")
    coating_usd = COATING_OPTIONS.get(coating_option, 0)
    coating_name = get_coating_name(coating_option)
    coating_uah = coating_usd * usd_rate
    engraving = data["engraving"]
    delivery = data["delivery"]
    discount_percent = data["discount_percent"]
    main_size = data["main_size"]
    main_qty = data["main_qty"]
    small_size = data["small_size"]
    small_qty = data["small_qty"]
    manual_weight = data.get("manual_weight", 0)

    auto_weight = calc_weight(size, width, thickness)
    total_weight = manual_weight if manual_weight > 0 else auto_weight
    weight_note = "Вага задана вручну" if manual_weight > 0 else "Вага розрахована автоматично"

    work_cost = total_weight * get_work_price("Каблучка")
    discount = work_cost * (discount_percent / 100)
    work_after_discount = work_cost - discount
    gold_cost = total_weight * GOLD_PRICE
    base_total_without_stones = gold_cost + work_after_discount + PACKAGING + engraving + coating_uah + delivery

    main_usd, main_uah = get_stone_cost_by_type("Натуральні діаманти", main_size, main_qty, usd_rate)
    small_usd, small_uah = get_stone_cost_by_type("Натуральні діаманти", small_size, small_qty, usd_rate)
    stones_usd = main_usd + small_usd
    stones_uah = main_uah + small_uah
    total = base_total_without_stones + stones_uah

    coating_client = coating_name
    inserts_text = make_inserts_text(main_size, main_qty, small_size, small_qty)

    technical_text = f"""Курс USD: {usd_rate:.2f} грн

Тип виробу:
Каблучка

Тип золота:
{gold_type} золото 585 проби

Покриття вибране:
{coating_option}

{weight_note}:
{total_weight:.2f} г

Загальна вага:
{total_weight:.2f} г

Золото:
{money(gold_cost)} грн

Робота:
{money(work_cost)} грн

Знижка:
-{money(discount)} грн

Робота після знижки:
{money(work_after_discount)} грн

Упаковка:
{money(PACKAGING)} грн

Гравіювання:
{money(engraving)} грн

Покриття:
{money(coating_uah)} грн

Діаманти / каміння:
{money(stones_uah)} грн ({stones_usd}$)

Доставка:
{money(delivery)} грн

=====================
ДО СПЛАТИ:
{money(total)} грн
"""

    variant_totals = {}
    for stone_type in STONE_PRICES_USD.keys():
        _, main_uah_variant = get_stone_cost_by_type(stone_type, main_size, main_qty, usd_rate)
        _, small_uah_variant = get_stone_cost_by_type(stone_type, small_size, small_qty, usd_rate)
        variant_totals[stone_type] = base_total_without_stones + main_uah_variant + small_uah_variant

    client_text = f"""Каблучка індивідуального дизайну ⚜️

{gold_type} золото 585 проби 💍
Розмір: {size:g}
Ширина: {width:g} мм
Покриття: {coating_client}
Середня вага виробу: {total_weight:.1f} г
Вставки: {inserts_text}

Середня вартість виробу:
• з натуральними діамантами:
{money100(variant_totals["Натуральні діаманти"])} грн 💎
• з лабораторними діамантами:
{money100(variant_totals["Лабораторні діаманти"])} грн 💎
• з муасанітами:
{money100(variant_totals["Муасаніти"])} грн 💎
"""

    receipt_data = {
        "title": "Каблучка індивідуального дизайну",
        "gold_type": f"{gold_type} золото 585 проби",
        "sizes": f"{size:g}",
        "width": f"{width:g} мм",
        "coating": coating_client,
        "weight": f"{total_weight:.1f} г",
        "inserts": inserts_text,
        "gold_cost": gold_cost,
        "work_cost": work_cost,
        "discount": discount,
        "packaging": PACKAGING,
        "engraving": engraving,
        "coating_cost": coating_uah,
        "stones_cost": stones_uah,
        "delivery": delivery,
        "total": total,
    }
    return technical_text, client_text, receipt_data



def render_client_receipt(receipt_data):
    """Виводить охайний чек для клієнта на основі технічного розрахунку."""
    if not receipt_data:
        st.info("Спочатку виконайте розрахунок, щоб сформувати чек.")
        return

    def safe(value):
        return html.escape(str(value))

    def row(label, value, negative=False):
        if not value:
            return ""
        css_class = "receipt-row negative" if negative else "receipt-row"
        sign = "−" if negative else ""
        return (
            f'<div class="{css_class}">'
            f'<span>{safe(label)}</span>'
            f'<strong>{sign}{money(value)} грн</strong>'
            f'</div>'
        )

    items_html = ""
    items_html += row("Золото", receipt_data.get("gold_cost", 0))
    items_html += row("Робота", receipt_data.get("work_cost", 0))
    items_html += row("Знижка", receipt_data.get("discount", 0), negative=True)
    #items_html += row("Упаковка", receipt_data.get("packaging", 0))
    items_html += row("Гравіювання", receipt_data.get("engraving", 0))
    items_html += row("Покриття", receipt_data.get("coating_cost", 0))
    items_html += row("Діаманти / каміння", receipt_data.get("stones_cost", 0))
    #items_html += row("Доставка", receipt_data.get("delivery", 0))

    receipt_number = datetime.now().strftime("%d%m%y-%H%M")
    receipt_date = datetime.now().strftime("%d.%m.%Y")

    receipt_html = f"""
    <!DOCTYPE html>
    <html lang="uk">
    <head>
    <meta charset="UTF-8">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 18px;
            background: #f4f4f2;
            font-family: Arial, Helvetica, sans-serif;
            color: #1d1d1d;
        }}
        .receipt {{
            width: 100%;
            max-width: 660px;
            margin: 0 auto;
            background: #ffffff;
            border: 1px solid #deded9;
            border-radius: 18px;
            padding: 34px 38px 30px;
            box-shadow: 0 14px 40px rgba(0,0,0,.08);
        }}
        .logo {{
            text-align: center;
            font-family: Georgia, serif;
            font-size: 30px;
            font-weight: 700;
            letter-spacing: 6px;
            margin-bottom: 5px;
        }}
        .brand {{
            text-align: center;
            font-size: 10px;
            letter-spacing: 4px;
            color: #777;
            margin-bottom: 28px;
        }}
        .receipt-title {{
            text-align: center;
            font-size: 13px;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: #777;
            margin-bottom: 8px;
        }}
        .product-title {{
            text-align: center;
            font-family: Georgia, serif;
            font-size: 22px;
            line-height: 1.3;
            margin-bottom: 24px;
        }}
        .meta {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            border-top: 1px dashed #bdbdb8;
            border-bottom: 1px dashed #bdbdb8;
            padding: 12px 0;
            margin-bottom: 22px;
            color: #6a6a66;
            font-size: 12px;
        }}
        .specs {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 11px 24px;
            padding-bottom: 22px;
            border-bottom: 1px solid #e5e5e1;
        }}
        .spec {{
            display: flex;
            justify-content: space-between;
            gap: 14px;
            font-size: 13px;
        }}
        .spec span:first-child {{ color: #777; }}
        .spec strong {{ text-align: right; font-weight: 600; }}
        .items {{
            padding: 18px 0 12px;
            border-bottom: 1px dashed #bdbdb8;
        }}
        .receipt-row {{
            display: flex;
            justify-content: space-between;
            gap: 18px;
            padding: 6px 0;
            font-size: 14px;
        }}
        .receipt-row strong {{ white-space: nowrap; }}
        .receipt-row.negative {{ color: #8b3d3d; }}
        .total {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            gap: 20px;
            padding-top: 22px;
        }}
        .total-label {{
            font-size: 12px;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #6c6c68;
        }}
        .total-value {{
            font-family: Georgia, serif;
            font-size: 31px;
            font-weight: 700;
            white-space: nowrap;
        }}
        .footer {{
            text-align: center;
            margin-top: 28px;
            padding-top: 17px;
            border-top: 1px solid #ecece8;
            color: #858581;
            font-size: 11px;
            line-height: 1.6;
        }}
        .print-button {{
            display: block;
            width: 100%;
            margin-top: 18px;
            padding: 13px 16px;
            border: 0;
            border-radius: 10px;
            background: #202020;
            color: white;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 1px;
            cursor: pointer;
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .receipt {{ box-shadow: none; border: none; }}
            .print-button {{ display: none; }}
        }}
    </style>
    </head>
    <body>
      <div class="receipt">
        <div class="logo">L&amp;L</div>
        <div class="brand">LANA &amp; LONA JEWELLERY</div>

        <div class="receipt-title">Персональний розрахунок</div>
        <div class="product-title">{safe(receipt_data.get("title", ""))}</div>

        <div class="meta">
          <span>№ {receipt_number}</span>
          <span>{receipt_date}</span>
        </div>

        <div class="specs">
          <div class="spec"><span>Золото</span><strong>{safe(receipt_data.get("gold_type", ""))}</strong></div>
          <div class="spec"><span>Розмір</span><strong>{safe(receipt_data.get("sizes", ""))}</strong></div>
          <div class="spec"><span>Ширина</span><strong>{safe(receipt_data.get("width", ""))}</strong></div>
          <div class="spec"><span>Покриття</span><strong>{safe(receipt_data.get("coating", ""))}</strong></div>
          <div class="spec"><span>Вага</span><strong>{safe(receipt_data.get("weight", ""))}</strong></div>
          <div class="spec"><span>Вставки</span><strong>{safe(receipt_data.get("inserts", "не додано"))}</strong></div>
        </div>

        <div class="items">{items_html}</div>

        <div class="total">
          <div class="total-label">До сплати</div>
          <div class="total-value">{money(receipt_data.get("total", 0))} грн</div>
        </div>

        <div class="footer">
          Розрахунок є орієнтовним і може уточнюватися після погодження всіх деталей виробу.<br>
          Дякуємо, що обираєте Lana &amp; Lona.
        </div>

        <button class="print-button" onclick="window.print()">ДРУКУВАТИ / ЗБЕРЕГТИ PDF</button>
      </div>
    </body>
    </html>
    """

    components.html(receipt_html, height=830, scrolling=True)


st.set_page_config(page_title="Калькулятор Lana & Lona", layout="wide")

if "screen" not in st.session_state:
    st.session_state.screen = "start"


def go_start():
    st.session_state.screen = "start"


def go_wedding():
    st.session_state.screen = "wedding"


def go_ring():
    st.session_state.screen = "ring"


st.markdown("""
<style>
.main-title {text-align:center; font-size:34px; font-weight:700; margin-top:40px;}
textarea {font-size:16px !important;}
</style>
""", unsafe_allow_html=True)

if st.session_state.screen == "start":
    st.markdown('<div class="main-title">Що потрібно прорахувати?</div>', unsafe_allow_html=True)
    st.write("")
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.button("Обручки", use_container_width=True, on_click=go_wedding)
        st.button("Каблучка", use_container_width=True, on_click=go_ring)

elif st.session_state.screen == "wedding":
    st.button("← Назад", on_click=go_start)
    st.title("Калькулятор обручок")
    left, right = st.columns([1, 1.4])

    with left:
        st.subheader("Дані для прорахунку")
        design = st.selectbox("Дизайн", ["Вишиванка", "Індивідуальний"])
        gold_type = st.selectbox("Тип золота", GOLD_TYPES, index=2, key="wedding_gold_type")
        st.markdown("### Обручка 1")
        size_1 = st.number_input("Розмір 1", min_value=1.0, value=16.0, step=0.5)
        width_1 = st.number_input("Ширина 1, мм", min_value=0.1, value=5.0, step=0.1)
        thickness_1 = st.number_input("Товщина 1, мм", min_value=0.1, value=1.2, step=0.1)
        use_second_ring = st.checkbox("Додати другу обручку", value=True)
        if use_second_ring:
            st.markdown("### Обручка 2")
            size_2 = st.number_input("Розмір 2", min_value=1.0, value=19.0, step=0.5)
            width_2 = st.number_input("Ширина 2, мм", min_value=0.1, value=5.0, step=0.1)
            thickness_2 = st.number_input("Товщина 2, мм", min_value=0.1, value=1.2, step=0.1)
        else:
            size_2 = width_2 = thickness_2 = 0.0
        st.markdown("### Вставки каміння")
        stone_sizes = list(STONE_PRICES_USD["Натуральні діаманти"].keys())
        ring_stone_enabled = st.checkbox("Додати діаманти в обручку")
        ring_stone_ring = st.selectbox("В яку обручку додати", [1, 2] if use_second_ring else [1], disabled=not ring_stone_enabled)
        ring_stone_size = st.selectbox("Розмір діаманта", stone_sizes, index=1, disabled=not ring_stone_enabled)
        ring_stone_qty = st.number_input("Кількість діамантів", min_value=0, value=0, step=1, disabled=not ring_stone_enabled)
        st.markdown("### Додатково")
        discount_percent = st.selectbox("Знижка, %", [0, 7, 10, 15, 20])
        coating_option = st.selectbox("Покриття", list(COATING_OPTIONS.keys()), key="wedding_coating_option")
        engraving = st.selectbox("Гравіювання, грн", [0, 800, 1500])
        delivery = st.number_input("Доставка, грн", min_value=0.0, value=0.0, step=100.0)
        calculate_btn = st.button("РОЗРАХУВАТИ", use_container_width=True)

    with right:
        current_auto_weight_1 = calc_weight(size_1, width_1, thickness_1)
        current_auto_weight_2 = calc_weight(size_2, width_2, thickness_2) if use_second_ring else 0.0
        if calculate_btn:
            st.session_state.wedding_manual_weight_1 = 0.0
            st.session_state.wedding_manual_weight_2 = 0.0
            technical_text, client_text, receipt_data = calculate_wedding_rings({
                "design": design, "gold_type": gold_type, "coating_option": coating_option, "use_second_ring": use_second_ring,
                "size_1": size_1, "width_1": width_1, "thickness_1": thickness_1, "manual_weight_1": 0.0,
                "size_2": size_2, "width_2": width_2, "thickness_2": thickness_2, "manual_weight_2": 0.0,
                "discount_percent": discount_percent, "engraving": engraving, "delivery": delivery,
                "ring_stone_enabled": ring_stone_enabled, "ring_stone_ring": ring_stone_ring, "ring_stone_size": ring_stone_size, "ring_stone_qty": ring_stone_qty,
            })
            st.session_state.technical_text = technical_text
            st.session_state.client_text = client_text
            st.session_state.receipt_data = receipt_data

        st.subheader("📊 Технічний розрахунок")
        st.caption("Тут менеджер може виправити вагу вручну і перерахувати ціну.")
        if use_second_ring:
            c1, c2 = st.columns(2)
            with c1:
                manual_weight_1_right = st.number_input("Вага виробу 1, г", min_value=0.0, value=st.session_state.get("wedding_manual_weight_1", 0.0) or current_auto_weight_1, step=0.1, format="%.2f", key="wedding_weight_input_1")
            with c2:
                manual_weight_2_right = st.number_input("Вага виробу 2, г", min_value=0.0, value=st.session_state.get("wedding_manual_weight_2", 0.0) or current_auto_weight_2, step=0.1, format="%.2f", key="wedding_weight_input_2")
        else:
            manual_weight_1_right = st.number_input("Вага виробу, г", min_value=0.0, value=st.session_state.get("wedding_manual_weight_1", 0.0) or current_auto_weight_1, step=0.1, format="%.2f", key="wedding_weight_input_1")
            manual_weight_2_right = 0.0

        if st.button("ПЕРЕРАХУВАТИ ПО ВАЗІ", use_container_width=True, key="recalculate_wedding_weight"):
            st.session_state.wedding_manual_weight_1 = manual_weight_1_right
            st.session_state.wedding_manual_weight_2 = manual_weight_2_right
            technical_text, client_text, receipt_data = calculate_wedding_rings({
                "design": design, "gold_type": gold_type, "coating_option": coating_option, "use_second_ring": use_second_ring,
                "size_1": size_1, "width_1": width_1, "thickness_1": thickness_1, "manual_weight_1": manual_weight_1_right,
                "size_2": size_2, "width_2": width_2, "thickness_2": thickness_2, "manual_weight_2": manual_weight_2_right,
                "discount_percent": discount_percent, "engraving": engraving, "delivery": delivery,
                "ring_stone_enabled": ring_stone_enabled, "ring_stone_ring": ring_stone_ring, "ring_stone_size": ring_stone_size, "ring_stone_qty": ring_stone_qty,
            })
            st.session_state.technical_text = technical_text
            st.session_state.client_text = client_text
            st.session_state.receipt_data = receipt_data

        st.text_area("Технічний текст", value=st.session_state.get("technical_text", ""), height=420)
        st.subheader("📋 Текст для клієнта")
        st.code(st.session_state.get("client_text", ""), language=None)
        st.caption("Натисни кнопку у правому верхньому куті блоку, щоб скопіювати текст.")
        st.subheader("🧾 Чек для клієнта")
        render_client_receipt(st.session_state.get("receipt_data"))

elif st.session_state.screen == "ring":
    st.button("← Назад", on_click=go_start)
    st.title("Калькулятор каблучки")
    left, right = st.columns([1, 1.4])
    with left:
        st.subheader("Дані для прорахунку")
        st.info("Для каблучки робота завжди рахується по 6100 грн/г. Дизайн тут не вибирається.")
        gold_type = st.selectbox("Тип золота", GOLD_TYPES, index=2, key="ring_gold_type")
        size = st.number_input("Розмір", min_value=1.0, value=16.0, step=0.5)
        width = st.number_input("Ширина, мм", min_value=0.1, value=2.5, step=0.1)
        thickness = st.number_input("Товщина, мм", min_value=0.1, value=1.2, step=0.1)
        st.markdown("### Вставки")
        stone_sizes = list(STONE_PRICES_USD["Натуральні діаманти"].keys())
        main_size = st.selectbox("Основний діамант — розмір", stone_sizes, index=0)
        main_qty = st.number_input("Основний діамант — к-сть", min_value=0, value=0, step=1)
        small_size = st.selectbox("Малі діаманти — розмір", stone_sizes, index=0)
        small_qty = st.number_input("Малі діаманти — к-сть", min_value=0, value=0, step=1)
        st.markdown("### Додатково")
        discount_percent = st.selectbox("Знижка, %", [0, 7, 10, 15, 20])
        coating_option = st.selectbox("Покриття", list(COATING_OPTIONS.keys()), key="ring_coating_option")
        engraving = st.selectbox("Гравіювання, грн", [0, 800, 1500])
        delivery = st.number_input("Доставка, грн", min_value=0.0, value=0.0, step=100.0)
        calculate_btn = st.button("РОЗРАХУВАТИ", use_container_width=True)

    with right:
        current_auto_weight = calc_weight(size, width, thickness)
        if calculate_btn:
            st.session_state.ring_manual_weight = 0.0
            technical_text, client_text, receipt_data = calculate_ring({
                "size": size, "width": width, "thickness": thickness, "gold_type": gold_type, "coating_option": coating_option, "manual_weight": 0.0,
                "main_size": main_size, "main_qty": main_qty, "small_size": small_size, "small_qty": small_qty,
                "discount_percent": discount_percent, "engraving": engraving, "delivery": delivery,
            })
            st.session_state.technical_text = technical_text
            st.session_state.client_text = client_text
            st.session_state.receipt_data = receipt_data

        st.subheader("📊 Технічний розрахунок")
        st.caption("Тут менеджер може виправити вагу вручну і перерахувати ціну.")
        manual_weight_right = st.number_input("Вага виробу, г", min_value=0.0, value=st.session_state.get("ring_manual_weight", 0.0) or current_auto_weight, step=0.1, format="%.2f", key="ring_weight_input")
        if st.button("ПЕРЕРАХУВАТИ ПО ВАГІ", use_container_width=True, key="recalculate_ring_weight"):
            st.session_state.ring_manual_weight = manual_weight_right
            technical_text, client_text, receipt_data = calculate_ring({
                "size": size, "width": width, "thickness": thickness, "gold_type": gold_type, "coating_option": coating_option, "manual_weight": manual_weight_right,
                "main_size": main_size, "main_qty": main_qty, "small_size": small_size, "small_qty": small_qty,
                "discount_percent": discount_percent, "engraving": engraving, "delivery": delivery,
            })
            st.session_state.technical_text = technical_text
            st.session_state.client_text = client_text
            st.session_state.receipt_data = receipt_data

        st.text_area("Технічний текст", value=st.session_state.get("technical_text", ""), height=420)
        st.subheader("📋 Текст для клієнта")
        st.code(st.session_state.get("client_text", ""), language=None)
        st.caption("Натисни кнопку у правому верхньому куті блоку, щоб скопіювати текст.")
        st.subheader("🧾 Чек для клієнта")
        render_client_receipt(st.session_state.get("receipt_data"))
