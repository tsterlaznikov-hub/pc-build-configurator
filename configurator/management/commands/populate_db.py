from django.core.management.base import BaseCommand
from configurator.models import Category, Component, CompatibilityRule


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми комплектующими'

    def handle(self, *args, **kwargs):
        self.stdout.write('Создаём категории...')
        categories = {
            'CPU': Category.objects.get_or_create(name='CPU', defaults={'slug': 'cpu', 'description': 'Процессоры'})[0],
            'GPU': Category.objects.get_or_create(name='GPU', defaults={'slug': 'gpu', 'description': 'Видеокарты'})[0],
            'Motherboard': Category.objects.get_or_create(name='Motherboard', defaults={'slug': 'motherboard', 'description': 'Материнские платы'})[0],
            'RAM': Category.objects.get_or_create(name='RAM', defaults={'slug': 'ram', 'description': 'Оперативная память'})[0],
            'PSU': Category.objects.get_or_create(name='PSU', defaults={'slug': 'psu', 'description': 'Блоки питания'})[0],
            'Case': Category.objects.get_or_create(name='Case', defaults={'slug': 'case', 'description': 'Корпуса'})[0],
            'Storage': Category.objects.get_or_create(name='Storage', defaults={'slug': 'storage', 'description': 'Накопители'})[0],
        }

        self.stdout.write('Создаём комплектующие...')
        components = [
            # CPU
            {'name': 'Core i5-13600K', 'category': 'CPU', 'brand': 'Intel', 'price_usd': 319.99,
             'specs': {'socket': 'LGA1700', 'cores': 14, 'tdp': 125, 'frequency': '3.5GHz'},
             'description': 'Мощный процессор для игр и работы'},
            {'name': 'Ryzen 5 7600X', 'category': 'CPU', 'brand': 'AMD', 'price_usd': 249.99,
             'specs': {'socket': 'AM5', 'cores': 6, 'tdp': 105, 'frequency': '4.7GHz'},
             'description': 'Отличный процессор для игр'},
            {'name': 'Ryzen 7 7700X', 'category': 'CPU', 'brand': 'AMD', 'price_usd': 349.99,
             'specs': {'socket': 'AM5', 'cores': 8, 'tdp': 105, 'frequency': '4.5GHz'},
             'description': 'Высокопроизводительный процессор'},
            {'name': 'Core i9-13900K', 'category': 'CPU', 'brand': 'Intel', 'price_usd': 549.99,
             'specs': {'socket': 'LGA1700', 'cores': 24, 'tdp': 253, 'frequency': '3.0GHz'},
             'description': 'Топовый процессор для энтузиастов'},

            # GPU
            {'name': 'RTX 4070', 'category': 'GPU', 'brand': 'NVIDIA', 'price_usd': 599.99,
             'specs': {'memory': '12GB', 'memory_type': 'GDDR6X', 'tdp': 200, 'pcie': 'PCIe 4.0'},
             'description': 'Отличная карта для 1440p gaming'},
            {'name': 'RTX 4060 Ti', 'category': 'GPU', 'brand': 'NVIDIA', 'price_usd': 399.99,
             'specs': {'memory': '8GB', 'memory_type': 'GDDR6', 'tdp': 165, 'pcie': 'PCIe 4.0'},
             'description': 'Хороший выбор для 1080p'},
            {'name': 'RX 7800 XT', 'category': 'GPU', 'brand': 'AMD', 'price_usd': 499.99,
             'specs': {'memory': '16GB', 'memory_type': 'GDDR6', 'tdp': 263, 'pcie': 'PCIe 4.0'},
             'description': 'Отличное соотношение цена/качество'},
            {'name': 'RTX 4090', 'category': 'GPU', 'brand': 'NVIDIA', 'price_usd': 1599.99,
             'specs': {'memory': '24GB', 'memory_type': 'GDDR6X', 'tdp': 450, 'pcie': 'PCIe 4.0'},
             'description': 'Самая мощная потребительская карта'},

            # Motherboard
            {'name': 'Z790 Aorus Elite', 'category': 'Motherboard', 'brand': 'Gigabyte', 'price_usd': 299.99,
             'specs': {'socket': 'LGA1700', 'form_factor': 'ATX', 'chipset': 'Z790', 'ram_slots': 4},
             'description': 'Топовая плата для Intel 13-го поколения'},
            {'name': 'X670E Steel Legend', 'category': 'Motherboard', 'brand': 'ASRock', 'price_usd': 279.99,
             'specs': {'socket': 'AM5', 'form_factor': 'ATX', 'chipset': 'X670E', 'ram_slots': 4},
             'description': 'Надёжная плата для AMD Ryzen 7000'},
            {'name': 'B650 Pro RS', 'category': 'Motherboard', 'brand': 'ASRock', 'price_usd': 179.99,
             'specs': {'socket': 'AM5', 'form_factor': 'mATX', 'chipset': 'B650', 'ram_slots': 4},
             'description': 'Бюджетная плата для AM5'},

            # RAM
            {'name': 'Vengeance DDR5 32GB', 'category': 'RAM', 'brand': 'Corsair', 'price_usd': 89.99,
             'specs': {'capacity': '32GB', 'type': 'DDR5', 'speed': '5600MHz', 'modules': 2},
             'description': 'Быстрая DDR5 память'},
            {'name': 'Trident Z5 32GB', 'category': 'RAM', 'brand': 'G.Skill', 'price_usd': 99.99,
             'specs': {'capacity': '32GB', 'type': 'DDR5', 'speed': '6000MHz', 'modules': 2},
             'description': 'Премиальная DDR5 память'},
            {'name': 'Fury Beast 16GB', 'category': 'RAM', 'brand': 'Kingston', 'price_usd': 49.99,
             'specs': {'capacity': '16GB', 'type': 'DDR4', 'speed': '3200MHz', 'modules': 2},
             'description': 'Надёжная DDR4 память'},

            # PSU
            {'name': 'RM850x', 'category': 'PSU', 'brand': 'Corsair', 'price_usd': 149.99,
             'specs': {'wattage': 850, 'efficiency': '80+ Gold', 'modular': 'Full', 'form_factor': 'ATX'},
             'description': 'Тихий и надёжный блок питания'},
            {'name': 'Toughpower GF3 1000W', 'category': 'PSU', 'brand': 'Thermaltake', 'price_usd': 179.99,
             'specs': {'wattage': 1000, 'efficiency': '80+ Gold', 'modular': 'Full', 'form_factor': 'ATX'},
             'description': 'Мощный БП для топовых сборок'},
            {'name': 'Focus GX-750', 'category': 'PSU', 'brand': 'Seasonic', 'price_usd': 129.99,
             'specs': {'wattage': 750, 'efficiency': '80+ Gold', 'modular': 'Full', 'form_factor': 'ATX'},
             'description': 'Качественный блок питания'},

            # Case
            {'name': 'H510', 'category': 'Case', 'brand': 'NZXT', 'price_usd': 89.99,
             'specs': {'form_factor': 'ATX', 'type': 'Mid Tower', 'color': 'Black'},
             'description': 'Стильный минималистичный корпус'},
            {'name': 'Meshify 2', 'category': 'Case', 'brand': 'Fractal Design', 'price_usd': 139.99,
             'specs': {'form_factor': 'ATX', 'type': 'Mid Tower', 'color': 'Black'},
             'description': 'Отличная вентиляция и простота сборки'},
            {'name': 'Pure Base 500DX', 'category': 'Case', 'brand': 'be quiet!', 'price_usd': 119.99,
             'specs': {'form_factor': 'ATX', 'type': 'Mid Tower', 'color': 'Black'},
             'description': 'Тихий корпус с подсветкой'},

            # Storage
            {'name': 'SSD 980 Pro 1TB', 'category': 'Storage', 'brand': 'Samsung', 'price_usd': 109.99,
             'specs': {'capacity': '1TB', 'type': 'NVMe', 'interface': 'PCIe 4.0', 'speed_read': '7000MB/s'},
             'description': 'Быстрый NVMe накопитель'},
            {'name': 'SN850X 2TB', 'category': 'Storage', 'brand': 'WD', 'price_usd': 179.99,
             'specs': {'capacity': '2TB', 'type': 'NVMe', 'interface': 'PCIe 4.0', 'speed_read': '7300MB/s'},
             'description': 'Быстрый и ёмкий накопитель'},
        ]

        created_count = 0
        for data in components:
            category = categories[data.pop('category')]
            obj, created = Component.objects.get_or_create(
                name=data['name'],
                brand=data['brand'],
                defaults={**data, 'category': category}
            )
            if created:
                created_count += 1

        self.stdout.write('Создаём правила совместимости...')
        cpu_cat = categories['CPU']
        mb_cat = categories['Motherboard']
        case_cat = categories['Case']

        CompatibilityRule.objects.get_or_create(
            name='Совместимость сокета CPU и материнской платы',
            defaults={
                'category_a': cpu_cat,
                'category_b': mb_cat,
                'spec_key': 'socket',
                'description': 'Сокет процессора должен совпадать с сокетом материнской платы.',
            }
        )

        CompatibilityRule.objects.get_or_create(
            name='Совместимость форм-фактора корпуса и материнской платы',
            defaults={
                'category_a': mb_cat,
                'category_b': case_cat,
                'spec_key': 'form_factor',
                'description': 'Форм-фактор материнской платы должен поддерживаться корпусом.',
            }
        )

        self.stdout.write(self.style.SUCCESS(
            f'Готово! Создано {created_count} комплектующих и правила совместимости.'
        ))