## 1.Architecture design
```mermaid
graph TD
  A["User Browser"] --> B["React Frontend Application"]
  B --> C["HTTP JSON API"]
  C --> D["Python FastAPI Backend"]
  D --> E["Clock Engine"]
  E --> F["Doubly Circular Linked List (60 ticks)"]

  subgraph "Frontend Layer"
    B
  end

  subgraph "Backend Layer"
    D
    E
    F
  end
```

## 2.Technology Description
- Frontend: React@18 + TypeScript + vite + (opcional) tailwindcss
- Backend: Python@3.11 + FastAPI + Uvicorn
- Database: None (settings en memoria; opcional persistir en archivo JSON)

## 3.Route definitions
| Route | Purpose |
|-------|---------|
| / | Página de Reloj (Inicio), render del reloj y controles |
| /settings | Ajustes de apariencia y movimiento |
| /about | Explicación del enfoque y guía de ejecución |

## 4.API definitions (If it includes backend services)

### 4.1 Core API

Get clock render state
```
GET /api/clock/state
```
Response (TypeScript types compartibles):
```ts
export type ClockHandAngles = {
  hourDeg: number;
  minuteDeg: number;
  secondDeg: number;
};

export type Tick = {
  index: number;      // 0..59
  deg: number;        // angle for tick mark
  isHourMark: boolean;
};

export type ClockState = {
  isoTime: string;            // e.g. 2026-04-27T12:34:56.000Z
  mode: "realtime" | "simulated";
  running: boolean;
  angles: ClockHandAngles;
  ticks: Tick[];              // 60 items
};
```

Update settings
```
POST /api/settings
```
Request:
| Param Name | Param Type | isRequired | Description |
|-----------|------------|------------|-------------|
| theme | "light" \| "dark" | true | UI theme |
| size | number | true | Clock pixel size |
| smoothMotion | boolean | true | Smooth vs tick motion |
| refreshHz | number | true | Render/update rate |
| timeZone | string | false | IANA tz or "local" |
| simulationSpeed | number | false | e.g. 1, 2, 10 |

Response:
| Param Name | Param Type | Description |
|-----------|------------|-------------|
| ok | boolean | Update result |

## 5.Server architecture diagram (If it includes backend services)
```mermaid
graph TD
  A["Frontend"] --> B["FastAPI Router Layer"]
  B --> C["Service: ClockService"]
  C --> D["ClockEngine"]
  D --> E["DoublyCircularList"]

  B --> F["Service: SettingsService"]

  subgraph "Server"
    B
    C
    D
    E
    F
  end
```

## 6.Data model(if applicable)
No se requiere base de datos para un MVP.
- Settings: estructura en memoria (y opcionalmente serializada a JSON).
- El estado del reloj se deriva del time source + engine, sin persistencia.
