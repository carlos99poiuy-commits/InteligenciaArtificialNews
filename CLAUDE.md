# CLAUDE.md — AI PULSE News Page
> Instrucciones para Claude Code: lee este archivo completo antes de ejecutar cualquier tarea.

---

## 🎯 OBJETIVO DEL PROYECTO

Generar y publicar automáticamente una página HTML estática llamada **AI PULSE** — un portal de noticias de Inteligencia Artificial con:
- Modo día / noche
- Español / Inglés (toggle instantáneo)
- Secciones por tema (Ciberseguridad, Desarrollo, Noticias Generales)
- Cards con links a videos, artículos e imágenes
- Diseño visual atractivo, emojis cómicos, ticker animado
- Deploy automático a **GitHub Pages**

---

## 📁 ESTRUCTURA DEL PROYECTO

```
ai-pulse/
├── index.html          ← Página principal (generar desde spec abajo)
├── CLAUDE.md           ← Este archivo
├── README.md           ← Auto-generado
└── .github/
    └── workflows/
        └── deploy.yml  ← GitHub Actions para auto-deploy
```

---

## 🚀 TAREAS QUE DEBE EJECUTAR CLAUDE CODE

### PASO 1 — Verificar prerequisitos
```bash
git --version
gh --version || echo "gh CLI no instalado, usar git manual"
node --version || true
```

### PASO 2 — Crear estructura del proyecto
```bash
mkdir -p ai-pulse/.github/workflows
cd ai-pulse
git init
git branch -M main
```

### PASO 3 — Generar index.html
Crear el archivo `ai-pulse/index.html` con el contenido completo especificado en la sección **HTML SPEC** de este documento.

### PASO 4 — Generar README.md
```bash
cat > ai-pulse/README.md << 'EOF'
# 🤖 AI PULSE — Portal de Noticias de Inteligencia Artificial

Página estática con noticias, videos y tendencias de IA.

## Features
- 🌙 Dark / Light mode
- 🌐 Español / English toggle
- 📱 Responsive
- ⚡ Animaciones CSS puras
- 🔗 Links a videos y artículos reales

## Deploy
GitHub Pages — rama `main`, carpeta raíz.

## URL
`https://<tu-usuario>.github.io/ai-pulse/`
EOF
```

### PASO 5 — Crear GitHub Actions workflow
Crear `.github/workflows/deploy.yml`:
```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
      - id: deployment
        uses: actions/deploy-pages@v4
```

### PASO 6 — Git commit & push
```bash
cd ai-pulse
git add .
git commit -m "feat: AI Pulse - portal de noticias IA con dark mode y i18n"

# Opción A: GitHub CLI (si está instalado)
gh repo create ai-pulse --public --source=. --remote=origin --push

# Opción B: Git manual (si el usuario ya tiene el repo creado)
# git remote add origin https://github.com/<USUARIO>/ai-pulse.git
# git push -u origin main
```

### PASO 7 — Activar GitHub Pages
```bash
# Con gh CLI:
gh api repos/<USUARIO>/ai-pulse/pages \
  --method POST \
  -f source.branch=main \
  -f source.path=/
```
Si no hay gh CLI, indicar al usuario que vaya a:
`Settings → Pages → Source: Deploy from branch → main → / (root)`

### PASO 8 — Mostrar URL final
```bash
echo "✅ Deploy completado!"
echo "🌐 URL: https://<USUARIO>.github.io/ai-pulse/"
echo "⏳ GitHub Pages tarda ~2 minutos en activarse por primera vez."
```

---

## 📋 VARIABLES A CONFIGURAR

Antes de ejecutar, Claude Code debe preguntar o inferir:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `GITHUB_USER` | Username de GitHub | `carlos-dev` |
| `REPO_NAME` | Nombre del repositorio | `ai-pulse` |
| `GH_TOKEN` | Token de GitHub (si no hay gh CLI) | `ghp_xxxx` |

Si el usuario corre `claude` desde la carpeta del proyecto, Claude Code detecta el directorio y pregunta confirmación antes de crear el repo.

---

## 🎨 HTML SPEC — CONTENIDO COMPLETO

> Claude Code debe generar `index.html` con EXACTAMENTE esta especificación:

### Meta
- `<title>`: `AI PULSE — Noticias de Inteligencia Artificial`
- Fuentes Google: `Bebas Neue`, `Space Mono`, `Sora`
- Favicon: emoji 🤖 via `<link rel="icon" href="data:image/svg+xml,...>`

### Diseño
- **Dark mode default** con CSS variables
- **Light mode** toggle (botón en header)
- **Colores dark**: bg `#0a0a0f`, accent `#00f5d4`, accent2 `#ff6b6b`, accent3 `#ffd166`
- **Colores light**: bg `#f0f0f5`, accent `#00b4a0`
- Noise texture overlay con SVG inline
- Scroll reveal con IntersectionObserver
- Ticker de noticias animado (CSS keyframes)
- Hover en cards: `translateY(-4px)` + glow border

### Componentes requeridos
1. **Header sticky** — Logo "AIPULSE", botón lang toggle, botón theme toggle
2. **Hero section** — Título gigante Bebas Neue, subtítulo, emoji animado
3. **Ticker** — Barra de noticias deslizante
4. **Breaking banner** — Aviso destacado
5. **Sección Ciberseguridad** — Badge "🔥 URGENTE"
6. **Sección Desarrollo** — Badge "🆕 TENDENCIA"
7. **Sección Noticias IA** — Badge "📈 TOP TEMAS"
8. **Meme dividers** — Bloques cómicos entre secciones
9. **Footer** — Logo grande, emojis, crédito

### i18n
- Atributo `data-lang="es"` y `data-lang="en"` en bloques
- `data-lang-inline="es/en"` para spans inline
- Body clase `lang-es` o `lang-en` controla visibilidad via CSS

---

## 📰 CONTENIDO — LINKS Y DESCRIPCIONES

### SECCIÓN: Ciberseguridad & IA

#### Card 1 — FEATURED (grid-column: 1/-1)
```
emoji: 🕵️‍♂️💻🔓
tipo: 📰 Noticia General
titulo_es: MYTHOS: Ciberseguridad en la Era de la IA
titulo_en: MYTHOS: Cybersecurity in the AI Era
desc_es: La inteligencia artificial está redefiniendo el panorama de la
  ciberseguridad. Los atacantes usan IA para malware sofisticado, phishing
  personalizado y exploits automatizados. Este video aborda los mitos más
  comunes sobre IA y seguridad y por qué toda empresa debe entender esta
  nueva realidad.
desc_en: Artificial intelligence is redefining the cybersecurity landscape.
  Attackers use AI for sophisticated malware, personalized phishing and
  automated exploits. This video addresses the most common myths about
  AI and security and why every company must understand this new reality.
link: https://www.facebook.com/share/v/1Cmyoeezo5/
platform: Facebook Video
```

---

### SECCIÓN: El Futuro del Desarrollo

#### Card 1
```
emoji: 📋✍️🚀
tipo: 🎥 Video · YouTube
titulo_es: Spec Driven Development: El Futuro de la Programación
titulo_en: Spec Driven Development: The Future of Programming
desc_es: ¿Y si en lugar de escribir código directamente, primero escribes una
  especificación detallada que la IA ejecuta? Spec Driven Development (SDD)
  es el paradigma que reemplaza al vibe coding. Aprende a estructurar prompts
  como specs formales y cómo los Tech Leads pueden acelerar equipos enteros
  sin perder control de la arquitectura.
desc_en: What if instead of writing code directly, you first write a detailed
  specification that AI executes? Spec Driven Development (SDD) is the
  paradigm replacing vibe coding. Learn to structure prompts as formal specs
  and how Tech Leads can accelerate entire teams without losing architectural
  control.
link: https://youtu.be/p2WA672HrdI?si=k2vWrlYoioGEN6A-
platform: YouTube
```

#### Card 2 (contexto)
```
emoji: 🎸💻😎
tipo: 💡 Contexto relacionado
titulo_es: ¿Qué es Vibe Coding y por qué ya no alcanza?
titulo_en: What is Vibe Coding and why is it no longer enough?
desc_es: El vibe coding — prompts vagos esperando que la IA adivine — funciona
  para proyectos pequeños. En sistemas enterprise como microservicios, AWS
  Step Functions o migraciones mainframe necesitas especificaciones antes
  de código. El SDD es la respuesta.
desc_en: Vibe coding — vague prompts hoping AI guesses right — works for small
  projects. In enterprise systems like microservices, AWS Step Functions or
  mainframe migrations you need specs before code. SDD is the answer.
link: https://youtu.be/p2WA672HrdI?si=k2vWrlYoioGEN6A-
platform: YouTube
```

---

### SECCIÓN: Lo que debes saber de IA (tarjetas editoriales, sin link externo)

#### Card 1
```
emoji: 🤖🧠⚡
tipo: 📌 Concepto clave
titulo_es: Agentes de IA: Ya no solo responden, actúan
titulo_en: AI Agents: They no longer just respond, they act
desc_es: Los LLMs pasaron de chatbots a agentes autónomos que navegan web,
  ejecutan código, gestionan archivos y coordinan otros agentes. El rol del
  desarrollador cambia: de escribir lógica a orquestar agentes especializados.
desc_en: LLMs went from chatbots to autonomous agents that browse the web,
  execute code, manage files and coordinate other agents. The developer's role
  shifts: from writing logic to orchestrating specialized agents.
platform: 🌐 General
```

#### Card 2
```
emoji: 🏦🔒💳
tipo: 🏢 IA en Empresas
titulo_es: IA en Banca: Entre la Innovación y el Riesgo
titulo_en: AI in Banking: Between Innovation and Risk
desc_es: Los bancos globales adoptan IA para detección de fraudes, onboarding
  digital y análisis de riesgo crediticio. Pero también enfrentan nuevos
  vectores de ataque. La doble cara de la tecnología más disruptiva del siglo.
desc_en: Global banks adopt AI for fraud detection, digital onboarding and
  credit risk analysis. But they also face new attack vectors. The double
  edge of the most disruptive technology of the century.
platform: 🏦 Fintech
```

#### Card 3
```
emoji: ⚖️🤖📜
tipo: ⚖️ Regulación
titulo_es: Regulación de IA: El mundo está tratando de ponerle reglas
titulo_en: AI Regulation: The world is trying to set rules
desc_es: La Unión Europea lanzó el AI Act, México y Latinoamérica aún debaten
  marcos normativos. Mientras tanto las empresas tecnológicas avanzan más
  rápido que los reguladores. ¿Quién ganará esta carrera?
desc_en: The EU launched the AI Act, Mexico and Latin America still debate
  regulatory frameworks. Meanwhile tech companies advance faster than
  regulators. Who will win this race?
platform: 🌍 Global
```

---

### MEME DIVIDERS (textos cómicos entre secciones)

```
Divider 1 (después de Ciberseguridad):
  emoji: 😱🔓🤖
  es: "Yo pensando que tenía buena contraseña..." vs la IA crackeándola en 0.3 segundos.
  en: "Me thinking I had a strong password..." vs the AI cracking it in 0.3 seconds.

Divider 2 (después de Desarrollo):
  emoji: 👨‍💻📝🤯
  es: Desarrollador en 2020: "Escribo el código" — 2025: "Escribo el spec y la IA escribe el código" — 2030: 🤔
  en: Developer in 2020: "I write the code" — 2025: "I write the spec, AI writes the code" — 2030: 🤔

Divider 3 (final):
  emoji: 🧠🚀🌮
  es: El futuro llegó y tiene tokens, embeddings y Step Functions. Bienvenido a la era IA. 🇲🇽
  en: The future arrived and it has tokens, embeddings and Step Functions. Welcome to the AI era. 🌎
```

---

### TICKER (noticias deslizantes)

```
🔴 CYBERSECURITY + IA = nueva era de amenazas
⚡ Spec Driven Development: el futuro del código
🤖 Los LLMs ya escriben mejor código que muchos devs
🛡️ Mythode AI: nueva frontera en ciberseguridad
🚀 Vibe Coding vs Spec Coding: ¿cuál gana?
🔴 CYBERSECURITY + AI = new threat era
⚡ Spec Driven Development: the future of code
🤖 LLMs already write better code than many devs
🛡️ Mythode AI: new frontier in cybersecurity
🚀 Vibe Coding vs Spec Coding: who wins?
```

---

## ⚙️ INSTRUCCIONES ESPECIALES PARA CLAUDE CODE

```
1. NO pedir confirmación en cada paso — ejecutar el flujo completo de corrido.
2. Si gh CLI no está disponible, hacer git init + git push con token de env.
3. Si el repo ya existe en GitHub, hacer git pull --rebase antes de push.
4. El archivo final se llama index.html (no ai-news.html) para que GitHub
   Pages lo sirva en la raíz sin especificar nombre de archivo.
5. Después del push, imprimir la URL pública al usuario.
6. Si hay errores de red/auth, mostrar el comando manual exacto a ejecutar.
7. Usar SIEMPRE rama "main" (no master).
```

---

## 🔑 AUTENTICACIÓN GITHUB — OPCIONES

### Opción A: GitHub CLI (recomendada)
```bash
gh auth login
# Sigue el wizard → GitHub.com → HTTPS → Browser
```

### Opción B: Token en variable de entorno
```bash
export GH_TOKEN=ghp_tuTokenAqui
git remote set-url origin https://x-access-token:${GH_TOKEN}@github.com/<USUARIO>/ai-pulse.git
git push -u origin main
```

### Opción C: Git credential helper (Windows/Mac)
```bash
git config --global credential.helper manager
git push  # abre ventana de login de GitHub
```

---

## 📝 CÓMO AGREGAR MÁS CONTENIDO EN EL FUTURO

Para agregar un nuevo video/artículo, dale a Claude Code este prompt:

```
Agrega a AI Pulse el siguiente contenido:
- Sección: [Ciberseguridad | Desarrollo | Noticias]
- Tipo: [Video YouTube | Facebook | Artículo | Imagen]
- Link: <url>
- Descripción ES: <texto>
- Descripción EN: <texto>
- Emoji banner: <emojis>

Luego haz commit y push automático.
```

Claude Code debe:
1. Leer `index.html` existente
2. Encontrar la sección correcta
3. Insertar el nuevo card en el grid
4. Hacer `git add . && git commit -m "content: add [título]" && git push`

---

## 🏁 COMANDO DE INICIO RÁPIDO

Copia y pega esto en tu terminal con Claude Code activo:

```
Por favor ejecuta el CLAUDE.md completo:
1. Crea la estructura del proyecto ai-pulse/
2. Genera el index.html con todo el contenido especificado
3. Crea el workflow de GitHub Actions
4. Inicializa git y sube el proyecto a GitHub
5. Muéstrame la URL final de GitHub Pages
Mi usuario de GitHub es: [REEMPLAZA CON TU USUARIO]
```

---

*Generado automáticamente · AI PULSE Project · 2025*
