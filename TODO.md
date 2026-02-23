# TODO — DM System

## Module System (Community Expansion Packs) 🔥 NEW

**Цель:** Модульная архитектура для включения/выключения механик при создании кампании

### Core Architecture

- [ ] **Module Registry** — `.claude/modules/registry.json` с метаданными всех доступных модулей
  - [ ] Поля: `id`, `name`, `version`, `description`, `author`, `dependencies`, `campaign_rules_patch`
  - [ ] Автоматическое сканирование `.claude/modules/*/module.json`
- [ ] **Module Loader** — `lib/module_loader.py` для активации модулей в кампании
  - [ ] Чтение `campaign-overview.json` → `enabled_modules: ["firearms", "survival"]`
  - [ ] Применение патчей к `campaign_rules` при загрузке кампании
  - [ ] Валидация зависимостей (если модуль A требует модуль B)
- [ ] **Interactive Setup** — `/new-game` спрашивает какие модули включить
  ```
  > Choose campaign type:
    1. Standard D&D (default — базовая механика)
    2. Modern/Firearms (STALKER, Fallout, Cyberpunk)
    3. Fantasy Extended (magic crafting, alchemy)
    4. Custom (выбрать модули вручную)

  > [Custom] Select modules:
    [✓] Coordinate Navigation (карта с координатами)
    [✓] Firearms Combat System (огнестрел, PEN/PROT)
    [ ] Survival Stats (голод/жажда/радиация)
    [✓] Encounter System (случайные встречи в пути)
    [ ] Magic Item Crafting (крафт магических предметов)
    [ ] Economic Simulation (торговля, рынки, инфляция)
  ```

### Module Structure

```
.claude/modules/
├── registry.json (auto-generated index)
├── firearms-system/
│   ├── module.json (metadata + dependencies)
│   ├── campaign_rules.json (weapons, fire_modes, armor)
│   ├── lib/combat_resolver.py (optional module-specific code)
│   └── README.md
├── survival-stats/
│   ├── module.json
│   ├── campaign_rules.json (time_effects, custom_stats)
│   └── README.md
└── coordinate-nav/
    ├── module.json
    ├── campaign_rules.json (encounter_system)
    └── README.md
```

### Example module.json

```json
{
  "id": "firearms-system",
  "name": "Modern Firearms Combat",
  "version": "1.0.0",
  "author": "DM System Core",
  "description": "Adds firearms with RPM-based combat, fire modes, and PEN vs PROT damage scaling",
  "dependencies": [],
  "requires_tools": ["dm-combat.sh"],
  "campaign_rules_patch": "./campaign_rules.json",
  "incompatible_with": ["medieval-only"]
}
```

### Implementation Tasks

- [ ] Рефакторинг: вынести firearms/survival/encounters из `modern-firearms-campaign.json` в отдельные модули
- [ ] `lib/module_loader.py` — загрузчик модулей с merge патчей в `campaign_rules`
- [ ] `tools/dm-module.sh list` — показать доступные модули
- [ ] `tools/dm-module.sh enable "firearms"` — добавить модуль к активной кампании
- [ ] `tools/dm-module.sh disable "survival"` — отключить модуль
- [ ] Обновить `/new-game` workflow для выбора модулей
- [ ] Документация: `.claude/docs/module-development-guide.md` для community

### Community Benefits

- ✅ Люди могут делать свои expansion pack'и (Sci-Fi, Horror, Economic)
- ✅ Backward compatibility — стандартные D&D кампании не захламлены
- ✅ Mix & Match — включай только нужные механики
- ✅ Версионирование модулей — обновления без поломки кампаний

---

## Quest System

- [ ] `dm-plot.sh add` — создание квестов через CLI (сейчас только ручной JSON)
- [ ] `dm-plot.sh objectives` — отметка выполненных целей внутри квеста
- [ ] `/dm quests` — отображение активных квестов игроку в красивом формате

## Map System

- [ ] `dm-map.sh` — полноценная ASCII-карта мира (глобальная) с координатами и масштабом
- [ ] Подкарты (submaps) — вложенные карты для локаций/объектов:
  - [ ] Интерьеры зданий, бункеров, пещер
  - [ ] Палубы космических кораблей / станций
  - [ ] Этажи подземелий
  - [ ] Переключение между глобальной картой и подкартой (`dm-map.sh --submap "Корабль"`)
- [ ] Связь между уровнями: лестницы, лифты, шлюзы, люки
- [ ] Хранение подкарт в `locations.json` (поле `submap` или отдельный `submaps.json`)

## Inventory System (Weight & Slots)

- [ ] `inventory.json` — отдельный файл вместо списка строк в `character.json`
  - [ ] Каждый предмет: `id`, `name`, `weight_kg`, `quantity`, `stackable`, `category`
  - [ ] Категории: weapon, ammo, medical, food, consumable, quest, junk, armor
  - [ ] Стакинг: патроны, бинты, еда суммируются автоматически
- [ ] Система веса:
  - [ ] Макс. грузоподъёмность = STR × 7 кг (базовая)
  - [ ] Рюкзак добавляет +10-15 кг к лимиту
  - [ ] Перегруз: скорость ×0.5, disadvantage на DEX, -2 к Скрытности
  - [ ] Критический перегруз (×2 лимита): движение 5ft/раунд
- [ ] `dm-player.sh inventory` — переписать на работу с `inventory.json`
  - [ ] `dm-player.sh inventory add "item" --qty 5` — добавление с количеством
  - [ ] `dm-player.sh inventory drop "item"` — выбросить (не удалить!)
  - [ ] `dm-player.sh inventory weight` — показать текущий вес / лимит
  - [ ] `dm-player.sh inventory list --category weapon` — фильтр по категории
- [ ] Автообъединение при добавлении (патроны 9мм + патроны 9мм = одна строка)
- [ ] Миграция: скрипт конвертации старого `equipment[]` в `inventory.json`
- [ ] 
- [ ] 
- [ ] 
- [ ]







 Я эсипи тип зеденый фодно охота макс сложно.