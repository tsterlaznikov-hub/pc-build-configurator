import logging
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from django.conf import settings
from django.core.cache import cache
from .models import Component, Category

logger = logging.getLogger(__name__)

EXCHANGE_RATE_API_URL_TEMPLATE = 'https://v6.exchangerate-api.com/v6/{api_key}/latest/USD'
CACHE_KEY = 'usd_rub_rate'
CACHE_TIMEOUT_SECONDS = 1800
FALLBACK_CACHE_TIMEOUT_SECONDS = 60
FALLBACK_RATE = 90.0


def get_usd_to_rub_rate():
    cached_rate = cache.get(CACHE_KEY)
    if cached_rate is not None:
        return cached_rate

    api_key = settings.EXCHANGE_RATE_API_KEY
    if not api_key:
        logger.warning(
            'EXCHANGE_RATE_API_KEY не настроен. Используется запасное значение %.2f',
            FALLBACK_RATE,
        )
        cache.set(CACHE_KEY, FALLBACK_RATE, timeout=FALLBACK_CACHE_TIMEOUT_SECONDS)
        return FALLBACK_RATE

    url = EXCHANGE_RATE_API_URL_TEMPLATE.format(api_key=api_key)

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get('result') != 'success':
            raise ValueError(f"API вернул ошибку: {data.get('error-type', 'неизвестная ошибка')}")

        rate = float(data['conversion_rates']['RUB'])
        cache.set(CACHE_KEY, rate, timeout=CACHE_TIMEOUT_SECONDS)
        logger.info('Курс USD/RUB обновлён из внешнего API: %.4f', rate)
        return rate
    except (requests.RequestException, KeyError, ValueError, TypeError) as exc:
        logger.warning(
            'Не удалось получить курс USD/RUB из внешнего API (%s). '
            'Используется запасное значение %.2f',
            exc, FALLBACK_RATE,
        )
        cache.set(CACHE_KEY, FALLBACK_RATE, timeout=FALLBACK_CACHE_TIMEOUT_SECONDS)
        return FALLBACK_RATE


def convert_to_rub(price_usd):
    rate = get_usd_to_rub_rate()
    return round(float(price_usd) * rate)


def check_compatibility(build):
    from .models import CompatibilityRule

    warnings = []
    components = list(build.components.select_related('category').all())
    rules = CompatibilityRule.objects.select_related('category_a', 'category_b').all()

    for rule in rules:
        components_a = [c for c in components if c.category == rule.category_a]
        components_b = [c for c in components if c.category == rule.category_b]

        if not components_a or not components_b:
            continue

        for comp_a in components_a:
            for comp_b in components_b:
                val_a = comp_a.specs.get(rule.spec_key)
                val_b = comp_b.specs.get(rule.spec_key)

                if val_a and val_b and val_a != val_b:
                    warnings.append({
                        'rule': rule.name,
                        'message': (
                            f'Несовместимость: {comp_a} ({val_a}) '
                            f'и {comp_b} ({val_b}). {rule.description}'
                        ),
                        'component_a': str(comp_a),
                        'component_b': str(comp_b),
                    })

    return warnings


def get_build_price_chart(build):
    rate = get_usd_to_rub_rate()
    components = build.components.select_related('category').all()

    if not components:
        return None

    labels = [str(c) for c in components]
    values = [round(float(c.price_usd) * rate) for c in components]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        textinfo='percent',
        hovertemplate='<b>%{label}</b><br>%{value:,.0f} ₽<br>%{percent}<extra></extra>',
    )])

    fig.update_layout(
        title='Распределение стоимости компонентов (₽)',
        showlegend=True,
        legend=dict(
            orientation='v',
            x=1.05,
            y=0.5,
            font=dict(size=11),
        ),
        height=400,
        margin=dict(t=50, b=20, l=20, r=150),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def get_analytics_charts():
    rate = get_usd_to_rub_rate()
    components = Component.objects.select_related('category').all()

    if not components:
        return None, None

    data = [
        {
            'category': c.category.name,
            'price_rub': round(float(c.price_usd) * rate),
            'brand': c.brand,
            'name': str(c),
        }
        for c in components
    ]
    df = pd.DataFrame(data)

    avg_by_category = df.groupby('category')['price_rub'].mean().reset_index()
    avg_by_category['price_rub'] = avg_by_category['price_rub'].round()
    fig1 = px.bar(
        avg_by_category,
        x='category',
        y='price_rub',
        title='Средняя цена компонентов по категориям (₽)',
        labels={'category': 'Категория', 'price_rub': 'Средняя цена (₽)'},
        color='category',
    )
    fig1.update_layout(
        height=400,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    avg_by_brand = df.groupby('brand')['price_rub'].mean().reset_index()
    avg_by_brand['price_rub'] = avg_by_brand['price_rub'].round()
    avg_by_brand = avg_by_brand.sort_values('price_rub', ascending=False).head(10)
    fig2 = px.bar(
        avg_by_brand,
        x='brand',
        y='price_rub',
        title='Средняя цена по производителям (₽)',
        labels={'brand': 'Производитель', 'price_rub': 'Средняя цена (₽)'},
        color='price_rub',
        color_continuous_scale='Blues',
    )
    fig2.update_layout(
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return (
        fig1.to_html(full_html=False, include_plotlyjs='cdn'),
        fig2.to_html(full_html=False, include_plotlyjs=False),
    )