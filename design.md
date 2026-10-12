# UI/UX Design System & Interface Specifications
## The Lenny Growth Assistant

**Version:** 1.1.0 (Design & Interface Specifications)  
**Author:** Forward Deployed Engineering Assessment Candidate  
**Status:** In Planning / Design Phase  
**Last Updated:** October 2026

---

## 1. Design Philosophy & Visual Aesthetics

The Lenny Growth Assistant is designed to feel **state-of-the-art, hyper-responsive, and visually stunning**. Drawing inspiration from modern AI engineering platforms (Linear, Raycast, Claude Artifacts, and Stripe), the interface balances dense tactical product information with sleek, distraction-free aesthetics.

### 1.1 Color Palette & Design Tokens

```
Background Dark (Primary):     #0B0F19 (Deep Slate Obsidian)
Surface Dark (Cards/Panels):   #131B2E (Glassmorphic Midnight Blue)
Border & Divider:              #232F4D (Subtle Slate Border)
Primary Accent (Indigo):       #6366F1 (Electric Indigo - Growth / AI Intelligence)
Secondary Accent (Emerald):    #10B981 (Growth Emerald - Citations & Success)
Tertiary Accent (Amber):       #F59E0B (Lenny Podcast Gold - Highlights & Badges)
Text Primary:                  #F8FAFC (Crisp White)
Text Secondary:                #94A3B8 (Cool Slate)
Text Muted:                    #64748B (Muted Charcoal)
Error / Destructive:           #EF4444 (Crimson Red)
```

### 1.2 Typography
- **UI / Headings / Interface**: `Inter` / `Plus Jakarta Sans` (Crisp legibility at small sizes, modern geometric feel).
- **Long-Form Essays & Reading**: `Merriweather` / `Charter` (Warm editorial serif for Ship 30 for 30 essays).
- **Code & Raw Artifacts**: `JetBrains Mono` / `Fira Code` (Monospaced with ligatures).

---

## 2. Layout & Workspace Architecture

The application adopts a **Dual-Pane Dynamic Split Workspace**:

*(Note: The ASCII mockup below is an illustrative UI layout blueprint; sample dialogue and widgets are mock placeholders).*

```
+----------------------------------------------------------------------------------------------------+
|  [Logo] The Lenny Growth Assistant     [Sessions]   |   [● Anthropic Claude 3.5]   [Theme] [Docs]  |
+-----------------------------------------------------+----------------------------------------------+
|  LEFT PANE: Chat & Strategy Exploration (50%)       |  RIGHT PANE: Artifact Viewer (50% Collapsible)|
|                                                     |                                              |
|  [Sidebar]  +-------------------------------------+ |  +-----------------------------------------+ |
|  • Session1 | Assistant:                         | |  | [Preview] [Code] [Split]  [Copy] [⬇] [⛶] [✕] | |
|  • Session2 | [Illustrative Answer with          | |  +-----------------------------------------+ |
|  • Session3 | Clickable Citation Pills [1]]      | |  |  <<< LIVE SANDBOXED IFRAME >>>          | |
|  + New Chat |                                     | |  |                                         | |
|             | ┌─────────────────────────────────┐ | |  |  +------------------------------------+ | |
|             | │ 📦 Artifact: Growth Calculator  │ | |  |  │  [Interactive Component Render]   │ | |
|             | │ Type: HTML/CSS Interactive Tool │ | |  |  │  [Input A: Metric Value]          │ | |
|             | │ [Open in Viewer ->]             │ | |  |  │  [Input B: Target Growth Lift]    │ | |
|             | └─────────────────────────────────┘ | |  |  │  >>> Projected Output Calculation │ | |
|             |                                     | |  |  +------------------------------------+ | |
|             | [Further grounded analysis...]      | |  |                                         | |
|             +-------------------------------------+ |  +-----------------------------------------+ |
|                                                     |                                              |
|  [ 💬 Ask a PM or Growth question...       [↑ Send] ] |  Status: Artifact v1.0 rendered in 24ms    |
+-----------------------------------------------------+----------------------------------------------+
```

---

## 3. Component Design Specifications

### 3.1 Header & Provider Indicator Pill
- **Position**: Fixed top navigation bar.
- **Provider Status Indicator**:
  - **Green Dot (`#10B981`)**: Provider Online & Ready (`Anthropic Claude 3.5 Sonnet` or `Ollama (Llama 3.1)`).
  - **Pulsing Amber Dot (`#F59E0B`)**: Agent actively querying transcripts / synthesizing tokens.
  - **Red Dot (`#EF4444`)**: Local Ollama server disconnected or API key missing.
- **Quick Switcher Dropdown**: Allows toggling between Local (`Ollama`) and Cloud (`Anthropic` / `OpenAI`) without reloading the page.

### 3.2 Chat Message Feed & Citation Pills
- **User Message**: Aligned right with subtle indigo border glow `#6366F1`.
- **Assistant Message**: Aligned left with Lenny avatar badge. Supports real-time markdown streaming (tables, callout blocks, code blocks).
- **Interactive Citation Pills (`[1]`, `[2]`)**:
  - Rendered as clickable pill badges in Emerald Green (`#10B981`).
  - **Hover Action**: Shows tooltip with source snippet.
  - **Click Action**: Opens slide-over **Citation Drawer** revealing full transcript excerpt, episode number, guest profile, and timestamp jump-link.
- **Embedded Artifact Cards**: When the agent creates an artifact, an interactive card appears directly inside the chat flow showing artifact title, type badge (`HTML Tool`, `Markdown Guide`, `Ship 30 Essay`), and a quick action to launch it in the Right Pane.

### 3.3 Dedicated Artifact Viewer (Right Pane)
- **Automatic Trigger**: Automatically slides into view whenever a new artifact is generated or clicked from chat.
- **Top Control Bar**:
  - **Title & Type Badge**: E.g., `⚡ Growth Metric Simulator` `[HTML/CSS]`.
  - **Tab Switcher**:
    1. **Preview Tab**: Renders executable HTML/CSS in an isolated sandbox or formatted Markdown.
    2. **Code Tab**: Displays clean, syntax-highlighted source code with copy-line features.
    3. **Split Tab**: Displays code on the left and live preview on the right.
  - **Action Toolbar**:
    - `📋 Copy Code`: Copies raw source to clipboard with toast confirmation.
    - `⬇ Download`: Downloads `.html`, `.md`, or `.txt` file locally.
    - `⛶ Fullscreen`: Maximizes the artifact viewer across the full window.
    - `✕ Close`: Collapses the right pane back to full-width chat mode.
- **Security Sandboxing**:
  - All HTML/CSS/JS artifacts run inside `<iframe sandbox="allow-scripts" />` with `srcdoc` to prevent cookie access, parent DOM pollution, or XSS execution.

### 3.4 "Ship 30 for 30" Essay Viewer Mode
When an essay artifact is active, the viewer switches to a bespoke editorial layout:
- **Headline / Hook Banner**: Bold, high-contrast headline.
- **Metadata Stats Bar**: Live Word Count Badge (e.g. `1,248 / 1,250 words`), Estimated Reading Time (`4 min read`), and Primary Topic.
- **Typography & Formatting**: Clean serif typography, generous line spacing (`1.75`), pull quotes, and bold lead-ins for effortless scanning.

---

## 4. UI States, Feedback & Micro-Interactions

### 4.1 Loading & Streaming States
- **Thinking Indicator**: A smooth shimmering wave animation indicating RAG vector retrieval before first token streams.
- **Token Streaming**: Smooth text interpolation without jarring layout shifts.
- **Artifact Compilation Indicator**: Pulsing skeleton loader inside the Artifact Viewer while code chunks are streaming.

### 4.2 Error Handling & Fallbacks
- **Local Model Unreachable**: If Ollama is selected but not running, a friendly banner appears: *"Ollama is unreachable at localhost:11434. Please start Ollama or switch to Cloud Provider in the header."*
- **No Grounded Transcript Matches**: When a query finds zero relevant transcript chunks, the assistant displays an informational callout: *"No direct match found in Lenny's transcripts for this query."*
- **Sandboxed Execution Error**: If generated HTML has syntax errors, an inline error banner displays line number and fallback raw code.

---

## 5. Accessibility (a11y) & Keyboard Shortcuts

- **WCAG 2.1 AA Compliance**: Contrast ratio > 4.5:1 for all text elements.
- **Keyboard Shortcuts**:
  - `Ctrl + Enter` / `Cmd + Enter`: Send prompt.
  - `Escape`: Close Artifact Viewer / Dismiss Citation Drawer.
  - `Ctrl + Shift + S`: Toggle Session Sidebar.
  - `Ctrl + Shift + A`: Toggle Artifact Viewer.
- **Screen Reader Support**: All icons have `aria-label`, buttons have descriptive labels, and live streams use `aria-live="polite"`.
