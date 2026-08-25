# Требования к системе генерации электрических схем через MCP

## 1. Цель проекта

Сделать простую систему, через которую AI-агент сможет создавать читаемые классические электрические принципиальные схемы без прямого управления GUI KiCad и без ручной работы с координатами проводов.

Основная идея:

```text
AI Agent
   ↓
MCP / high-level API
   ↓
Semantic schematic model
   ↓
Validation / ERC
   ↓
Automatic layout
   ↓
SVG and/or KiCad schematic
```

Агент должен работать с понятиями:

- компонент;
- вывод компонента;
- электрическая сеть;
- соединение;
- группа компонентов;
- подсказка по расположению.

Агент не должен напрямую заниматься рисованием линий, вычислением координат пинов или редактированием формата `.kicad_sch`.

---

## 2. Основной сценарий использования

Пример пользовательского запроса:

> Нарисуй схему подключения INA226 к ESP32 по I2C. Добавь питание 3.3 В, землю, pull-up резисторы 4.7 кОм на SDA/SCL и разъём питания.

Ожидаемое поведение системы:

1. Агент ищет компоненты в библиотеке.
2. Получает список доступных выводов.
3. Создаёт экземпляры компонентов.
4. Соединяет конкретные выводы через именованные nets.
5. Выполняет валидацию.
6. Система автоматически размещает компоненты.
7. Система автоматически прокладывает линии.
8. Генерируется SVG.
9. По возможности генерируется редактируемая схема KiCad.

---

## 3. MVP

Первая версия должна уметь:

- искать компоненты;
- получать описание компонента и его выводов;
- создавать экземпляры компонентов;
- удалять компоненты;
- соединять выводы;
- создавать именованные сети;
- отключать выводы;
- проверять корректность ссылок на выводы;
- выполнять базовый ERC;
- автоматически размещать элементы;
- генерировать SVG;
- сохранять и загружать схему из простого декларативного формата;
- по возможности экспортировать `.kicad_sch`.

Редактирование PCB, footprints и трассировка платы в MVP не нужны.

---

## 4. Предпочтительный стек

### Базовый вариант

Использовать:

- Python;
- SKiDL как слой работы с компонентами, пинами, netlist и ERC;
- официальные библиотеки символов KiCad как базу компонентов;
- MCP server поверх собственного semantic API;
- SVG как основной формат предпросмотра;
- генерацию `.kicad_sch` через SKiDL, если качество устраивает.

### Если автоматический layout SKiDL окажется недостаточным

Оставить semantic model и MCP API без изменений, а визуальный backend заменить или дополнить:

- Schemdraw — для рендеринга классических символов и IC-блоков;
- ELK / elkjs — для автоматического размещения блоков и ортогональной маршрутизации;
- при необходимости отдельным алгоритмом orthogonal routing.

Архитектура должна позволять менять renderer без изменения MCP API.

---

## 5. Внутренняя модель данных

Нельзя использовать `.kicad_sch` как основной внутренний формат.

Нужен собственный простой декларативный формат.

Пример:

```json
{
  "components": [
    {
      "id": "U1",
      "library_id": "MCU_Espressif:ESP32-WROOM-32",
      "label": "ESP32",
      "value": "ESP32-WROOM-32"
    },
    {
      "id": "U2",
      "library_id": "Sensor_Current:INA226",
      "label": "INA226",
      "value": "INA226"
    },
    {
      "id": "R1",
      "library_id": "Device:R",
      "value": "4.7k"
    }
  ],
  "nets": [
    {
      "name": "I2C_SDA",
      "nodes": [
        "U1.GPIO21",
        "U2.SDA",
        "R1.1"
      ]
    }
  ]
}
```

Допускается другой JSON/YAML-формат, если он остаётся:

- простым;
- стабильным;
- читаемым человеком;
- независимым от KiCad;
- удобным для генерации LLM.

---

## 6. Модель компонента

Каждый компонент должен иметь:

```text
Component
- id
- library_id
- reference
- value
- label
- pins[]
- metadata
- placement_hint
```

Каждый pin:

```text
Pin
- number
- name
- electrical_type
- side
- orientation
- hidden
```

Для простых автоматически создаваемых IC-блоков желательно поддержать:

- pins слева;
- pins справа;
- pins сверху;
- pins снизу;
- отображение номера вывода;
- отображение имени вывода.

Пример:

```text
          U1 ESP32
      ┌──────────────┐
  3V3 ┤1          38 ├ GND
  SDA ┤21         23 ├ MOSI
  SCL ┤22         19 ├ MISO
      └──────────────┘
```

---

## 7. Электрическая модель и визуальное представление должны быть разделены

Критически важно разделить:

### Electrical model

Определяет:

- какие компоненты существуют;
- какие выводы существуют;
- какие выводы электрически соединены;
- какие сети имеют имена.

### Visual layout

Определяет:

- где расположен компонент;
- на какой стороне отображается pin;
- где проходят линии;
- где используются net labels.

Изменение расположения компонентов не должно менять электрическую схему.

---

## 8. Требования к MCP API

API должен быть высокоуровневым.

Предпочтительные MCP tools:

### Библиотека

```text
search_components(query)
get_component(component_id)
get_component_pins(component_id)
```

### Работа со схемой

```text
create_schematic(name)
load_schematic(path)
save_schematic(path)

add_component(library_id, reference?, value?)
remove_component(component_id)
set_component_value(component_id, value)
```

### Соединения

```text
connect(pin_a, pin_b)
connect_net(net_name, pins[])
disconnect(pin)
rename_net(old_name, new_name)
```

Где pin задаётся семантически:

```text
U1.GPIO21
U2.SDA
R1.1
```

А не через координаты.

### Layout

```text
set_placement_hint(component, relation, target)
set_pin_side(component, pin, side)
group_components(group_name, components[])
auto_layout()
```

Примеры placement hints:

```text
left_of
right_of
above
below
near
same_row
same_column
```

### Проверка

```text
validate()
run_erc()
```

### Вывод

```text
render_svg()
export_kicad()
get_preview()
```

---

## 9. Чего MCP API делать не должен

Не давать агенту низкоуровневые инструменты вида:

```text
move_component(x, y)
draw_wire(x1, y1, x2, y2)
click(x, y)
drag(...)
```

Если координаты всё же понадобятся, они должны быть опциональным escape hatch, а не основным способом построения схемы.

---

## 10. Правила автоматического layout

Система должна стараться соблюдать классические соглашения электрических схем.

### Общее направление

- поток сигнала: слева направо;
- входы: слева;
- выходы: справа;
- питание: сверху;
- земля: снизу.

### Компоненты

- связанные компоненты располагать рядом;
- pull-up/pull-down резисторы размещать рядом с соответствующей сетью;
- decoupling capacitors располагать рядом с питаемым компонентом;
- разъёмы обычно размещать по краям схемы;
- блоки питания — слева или сверху;
- нагрузку — справа.

### Провода

- только горизонтальные и вертикальные сегменты;
- минимизировать число изгибов;
- минимизировать пересечения;
- избегать длинных проводов через всю схему;
- использовать net labels, если физическое соединение ухудшает читаемость;
- избегать четырёхсторонних junctions;
- явно отображать junction dot там, где соединение действительно существует.

---

## 11. Net labels

Система должна уметь автоматически заменять неудобные длинные соединения на labels.

Например, вместо:

```text
U1 ───────────────────────────────────────── U8
```

допустимо:

```text
U1 ─ SDA

SDA ─ U8
```

При этом electrical model должна считать это одной сетью.

Особенно полезно для:

- GND;
- +3V3;
- +5V;
- I2C;
- SPI;
- UART;
- enable/control lines;
- соединений между удалёнными функциональными блоками.

---

## 12. Валидация

Перед рендерингом система должна проверять:

- существует ли компонент;
- существует ли указанный pin;
- нет ли дубликатов reference;
- нет ли двух разных net names на одной физической сети;
- нет ли очевидных конфликтов output-to-output;
- подключены ли обязательные power pins;
- нет ли случайно оставленных выводов;
- нет ли short между различными power rails.

Ошибки должны возвращаться агенту в структурированном виде.

Пример:

```json
{
  "errors": [
    {
      "type": "unknown_pin",
      "component": "U1",
      "pin": "GPIO99"
    }
  ],
  "warnings": [
    {
      "type": "unconnected_pin",
      "component": "U2",
      "pin": "ALERT"
    }
  ]
}
```

---

## 13. Поведение AI-агента

Перед изменением схемы агент должен:

1. Найти компонент.
2. Проверить реальные имена/номера выводов.
3. Не угадывать pin names, если библиотека доступна.
4. Создать логическую netlist.
5. Запустить validation/ERC.
6. Только после успешной проверки запускать layout/render.

Агент не должен самостоятельно придумывать физические координаты схемы, если система может выполнить layout автоматически.

---

## 14. Skill для агента

В проект желательно добавить `SKILL.md` с правилами работы со схемами.

Минимальные инструкции:

```text
- Always build the electrical netlist before layout.
- Never invent component pins.
- Query component data before connecting pins.
- Prefer semantic pin names over coordinates.
- Run validation after every significant edit.
- Signal flow should generally go left to right.
- Power rails go to the top, ground to the bottom.
- Prefer short local wires.
- Use net labels for distant connections.
- Avoid wire crossings.
- Do not manually route wires unless automatic layout fails.
- Rendering errors must never be fixed by changing the electrical netlist unless the netlist is actually wrong.
```

---

## 15. Работа с библиотеками KiCad

На первом этапе использовать существующие символы KiCad.

Нужно реализовать слой:

```text
KiCad symbol library
        ↓
component importer
        ↓
normalized Component + Pin model
```

Системе в первую очередь нужны:

- имя компонента;
- reference prefix;
- pin number;
- pin name;
- electrical pin type.

Для собственного block-renderer необязательно полностью воспроизводить графику KiCad-символа.

Например, сложный MCU можно автоматически рисовать прямоугольником с правильно подписанными выводами.

---

## 16. Два режима отображения компонентов

Желательно в будущем иметь:

### Classical mode

Для:

- resistor;
- capacitor;
- diode;
- transistor;
- MOSFET;
- op-amp;
- power symbols;
- switches.

Использовать привычные условные обозначения.

### Block mode

Для:

- MCU;
- sensors;
- modules;
- connectors;
- драйверов;
- сложных IC.

Прямоугольный блок с подписанными выводами.

Это позволит получить читаемую схему без необходимости поддерживать тысячи сложных SVG-символов.

---

## 17. Renderer

Renderer получает:

```text
semantic schematic
+
layout
```

и выдаёт SVG.

Renderer не должен определять электрическую связность.

Минимальные требования к SVG:

- vector output;
- текст остаётся текстом;
- масштабирование без потери качества;
- читаемые pin names;
- читаемые component values;
- junction dots;
- net labels;
- ортогональные линии.

---

## 18. Автоматический layout

Первый вариант:

- попробовать встроенную генерацию schematic в SKiDL.

Если качество недостаточное:

```text
semantic model
    ↓
graph builder
    ↓
ELK
    ↓
node positions
    ↓
wire routing
    ↓
Schemdraw/SVG renderer
```

При необходимости placement и routing можно разделить:

```text
ELK -> размещение компонентов
orthogonal router -> линии
```

---

## 19. Экспорт KiCad

KiCad должен рассматриваться как дополнительный backend, а не основной API системы.

Желательный workflow:

```text
JSON schematic
    ↓
export
    ↓
.kicad_sch
```

Это позволит открыть итоговую схему в KiCad и при необходимости вручную поправить её.

Однако отсутствие рабочего KiCad export не должно блокировать MVP.

---

## 20. CLI

Помимо MCP желательно иметь CLI.

Примеры:

```bash
schematic search INA226
schematic validate project.json
schematic render project.json -o project.svg
schematic export-kicad project.json -o project.kicad_sch
```

Это упростит:

- отладку;
- автоматические тесты;
- использование без MCP;
- работу агента через shell.

---

## 21. Тестирование

Нужны автоматические тесты как минимум для:

### Model

- добавление компонента;
- удаление компонента;
- соединение двух pins;
- именованные nets;
- merge nets;
- disconnect.

### Validation

- unknown component;
- unknown pin;
- duplicate reference;
- incompatible nets.

### Renderer

Golden tests:

```text
input JSON -> expected SVG
```

Не обязательно сравнивать SVG byte-to-byte.

Можно проверять:

- количество компонентов;
- наличие текста;
- наличие nets;
- отсутствие пересечений через компоненты;
- корректные endpoints проводов.

---

## 22. Пример первого demo

Первый end-to-end тест:

```text
ESP32
+
INA226
+
2 × 4.7k pull-up
+
0.1 uF decoupling
+
power connector
```

Соединения:

```text
ESP32 GPIO21 -> INA226 SDA
ESP32 GPIO22 -> INA226 SCL

3V3 -> INA226 VS
3V3 -> R1
3V3 -> R2

R1 -> SDA
R2 -> SCL

GND -> ESP32 GND
GND -> INA226 GND
```

Система должна самостоятельно получить схему приблизительно такого вида:

```text
       +3V3
        │
       ┌┴┐
       │ │ R1
       └┬┘
        ├──────── SDA
       ┌┴┐
       │ │ R2
       └┬┘
        └──────── SCL


 ┌──────────────┐          ┌──────────────┐
 │    ESP32     │          │    INA226    │
 │              │          │              │
 │ GPIO21 / SDA ├──────────┤ SDA          │
 │ GPIO22 / SCL ├──────────┤ SCL          │
 │              │          │              │
 │          GND ├── GND ───┤ GND          │
 └──────────────┘          └──────────────┘
```

Точное расположение может отличаться.

---

## 23. Предлагаемая структура проекта

```text
schematic-mcp/
├── README.md
├── SKILL.md
├── pyproject.toml
│
├── schematic/
│   ├── model.py
│   ├── library.py
│   ├── validation.py
│   ├── layout.py
│   ├── routing.py
│   ├── renderer.py
│   └── exporters/
│       ├── svg.py
│       └── kicad.py
│
├── mcp_server/
│   ├── server.py
│   └── tools.py
│
├── cli/
│   └── main.py
│
├── examples/
│   └── esp32_ina226.json
│
└── tests/
```

Не нужно сразу создавать все модули. Это целевая структура.

---

## 24. Приоритет разработки

### Этап 1

Сделать минимальный semantic model:

```text
Component
Pin
Net
Schematic
```

Плюс JSON save/load.

### Этап 2

Подключить KiCad library / SKiDL.

Реализовать:

```text
search_component
get_component_pins
add_component
connect
validate
```

### Этап 3

Сделать CLI и SVG render.

### Этап 4

Добавить MCP server.

### Этап 5

Добавить автоматический layout и правила оформления.

### Этап 6

Попробовать `.kicad_sch` export.

### Этап 7

Только если качество SVG не устраивает — делать собственный renderer/layout поверх Schemdraw + ELK.

---

## 25. Что не нужно делать на первом этапе

Не делать:

- PCB editor;
- footprint editor;
- PCB autorouter;
- SPICE;
- BOM management;
- полноценную замену KiCad;
- GUI schematic editor;
- collaborative editing;
- cloud storage;
- drag-and-drop;
- собственную огромную библиотеку компонентов.

Главная задача:

> AI должен надёжно описывать электрические соединения через простой semantic API, а программа должна превращать их в аккуратную схему.

---

## 26. Критерий успешного MVP

MVP считается успешным, если агент по текстовому запросу может без ручного редактирования:

1. найти нужные компоненты;
2. корректно определить их pins;
3. создать netlist;
4. пройти validation;
5. создать читаемый SVG;
6. сохранить исходную семантическую схему;
7. повторно открыть её и изменить через MCP.

Качество схемы должно быть достаточным, чтобы человек мог быстро понять соединения без просмотра исходного JSON.

---

## 27. Основной архитектурный принцип

Главное правило проекта:

```text
LLM decides WHAT is connected.
Software decides HOW it is drawn.
```

AI отвечает за смысл схемы.

Детерминированный код отвечает за геометрию.
